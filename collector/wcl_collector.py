import argparse
import json
import os
import re
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv


load_dotenv()
OAUTH_URL = "https://cn.warcraftlogs.com/oauth/token"
GRAPHQL_URL = "https://cn.warcraftlogs.com/api/v2/client"
DEFAULT_OUTPUT_DIR = os.path.join("data", "reports")
DEFAULT_WINDOW_MS = 10 * 60 * 1000
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_PAGES_PER_WINDOW = 100
DEFAULT_DATA_TYPE = "Casts"
VALID_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")
VALID_REPORT_CODE_RE = re.compile(r"^[A-Za-z0-9]+$")


class WCLCollectorError(RuntimeError):
    pass


class WCLClient(object):
    def __init__(self, client_id, client_secret, timeout=DEFAULT_TIMEOUT):
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self._access_token = None
        self.session = requests.Session()
        self.base_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

    def _build_headers(self, headers=None):
        merged = dict(self.base_headers)
        if headers:
            merged.update(headers)
        return merged

    def post_request(self, url, data, headers=None, timeout=None):
        request_timeout = timeout or self.timeout
        request_headers = self._build_headers(headers)
        try:
            if isinstance(data, (dict, list)):
                response = self.session.post(
                    url,
                    json=data,
                    headers=request_headers,
                    timeout=request_timeout,
                )
            else:
                response = self.session.post(
                    url,
                    data=data,
                    headers=request_headers,
                    timeout=request_timeout,
                )
        except requests.RequestException as exc:
            raise WCLCollectorError("网络请求失败: %s" % exc)

        if response.status_code >= 400:
            raise WCLCollectorError("HTTP %s: %s" % (response.status_code, response.text))
        return response.text

    @staticmethod
    def _is_auth_error(payload):
        for error in payload.get("errors") or []:
            message = str(error.get("message") or "").lower()
            if "unauth" in message or "token" in message or "auth" in message:
                return True
        return False

    def get_access_token(self, force_refresh=False):
        if self._access_token and not force_refresh:
            return self._access_token

        try:
            response = self.session.post(
                OAUTH_URL,
                data={"grant_type": "client_credentials"},
                auth=(self.client_id, self.client_secret),
                headers=self._build_headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise WCLCollectorError("Token 请求失败: %s" % exc)

        if response.status_code != 200:
            raise WCLCollectorError("Token 获取失败 HTTP %s: %s" % (response.status_code, response.text))

        data = response.json()
        access_token = data.get("access_token")
        if not access_token:
            raise WCLCollectorError("WCL 未返回 access_token。")
        self._access_token = access_token
        return access_token

    def graphql(self, query):
        access_token = self.get_access_token()
        request_headers = {
            "Authorization": "Bearer %s" % access_token,
            "Content-Type": "application/json",
        }

        try:
            response = self.session.post(
                GRAPHQL_URL,
                json={"query": query},
                headers=self._build_headers(request_headers),
                timeout=max(self.timeout, 60),
            )
        except requests.RequestException as exc:
            raise WCLCollectorError("网络请求失败: %s" % exc)

        # Token 过期或鉴权异常时，强制刷新并重试一次。
        if response.status_code == 401:
            access_token = self.get_access_token(force_refresh=True)
            request_headers["Authorization"] = "Bearer %s" % access_token
            try:
                response = self.session.post(
                    GRAPHQL_URL,
                    json={"query": query},
                    headers=self._build_headers(request_headers),
                    timeout=max(self.timeout, 60),
                )
            except requests.RequestException as exc:
                raise WCLCollectorError("网络请求失败: %s" % exc)

        if response.status_code >= 400:
            raise WCLCollectorError("HTTP %s: %s" % (response.status_code, response.text))

        payload = response.json()
        if payload.get("errors") and self._is_auth_error(payload):
            access_token = self.get_access_token(force_refresh=True)
            request_headers["Authorization"] = "Bearer %s" % access_token
            try:
                retry_response = self.session.post(
                    GRAPHQL_URL,
                    json={"query": query},
                    headers=self._build_headers(request_headers),
                    timeout=max(self.timeout, 60),
                )
            except requests.RequestException as exc:
                raise WCLCollectorError("网络请求失败: %s" % exc)

            if retry_response.status_code >= 400:
                raise WCLCollectorError("HTTP %s: %s" % (retry_response.status_code, retry_response.text))
            payload = retry_response.json()

        if payload.get("errors"):
            raise WCLCollectorError("GraphQL 返回错误: %s" % json.dumps(payload["errors"], ensure_ascii=False))
        if "data" not in payload:
            raise WCLCollectorError("GraphQL 响应缺少 data 字段。")
        return payload["data"]

    def fetch_report_metadata(self, report_code):
        query = """
        query {
          reportData {
            report(code: %s) {
              startTime
              endTime
              fights {
                id
                name
                startTime
                endTime
                kill
                bossPercentage
              }
            }
          }
        }
        """ % json.dumps(report_code)

        data = self.graphql(query)
        report = data.get("reportData", {}).get("report")
        if not report:
            raise WCLCollectorError("未找到报告 %s，请检查报告代码是否正确。" % report_code)
        return report

    def fetch_events_page(self, report_code, data_type, start_time, end_time):
        query = """
        query {
          reportData {
            report(code: %s) {
              events(dataType: %s, startTime: %d, endTime: %d) {
                data
                nextPageTimestamp
              }
            }
          }
        }
        """ % (json.dumps(report_code), data_type, int(start_time), int(end_time))

        data = self.graphql(query)
        report = data.get("reportData", {}).get("report")
        if not report or not report.get("events"):
            raise WCLCollectorError("未获取到事件数据，请确认报告窗口与 dataType 是否有效。")
        return report["events"]


def get_credentials():
    client_id = os.environ.get("WCL_CLIENT_ID", "").strip()
    client_secret = os.environ.get("WCL_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise WCLCollectorError(
            "缺少 WCL 凭证。请在项目根目录 .env 中配置 WCL_CLIENT_ID/WCL_CLIENT_SECRET，或先在系统环境变量中设置后再运行。"
        )
    if client_id == "your_client_id" or client_secret == "your_client_secret":
        raise WCLCollectorError(
            ".env 仍是示例占位符，请把 WCL_CLIENT_ID/WCL_CLIENT_SECRET 替换为你的真实凭证。"
        )
    return client_id, client_secret


def prompt_input(message):
    return input(message)


def ensure_valid_report_code(report_code):
    report_code = (report_code or "").strip()
    if not report_code:
        raise WCLCollectorError("报告代码不能为空。")
    if not VALID_REPORT_CODE_RE.match(report_code):
        raise WCLCollectorError("报告代码格式无效，只允许字母和数字。")
    return report_code


def ensure_valid_data_type(data_type):
    data_type = (data_type or "").strip()
    if not data_type:
        raise WCLCollectorError("dataType 不能为空。")
    if not VALID_NAME_RE.match(data_type):
        raise WCLCollectorError("dataType 格式无效，例如 Casts / DamageDone / Deaths。")
    return data_type


def parse_fight_ids(raw_values):
    fight_ids = []
    for raw_value in raw_values or []:
        for part in str(raw_value).split(","):
            value = part.strip()
            if not value:
                continue
            try:
                fight_id = int(value)
            except ValueError:
                raise WCLCollectorError("fight-id 必须是整数，收到: %s" % value)
            if fight_id not in fight_ids:
                fight_ids.append(fight_id)
    return fight_ids


def normalize_fights(fights):
    normalized = []
    for fight in fights or []:
        start_time = int(fight.get("startTime") or 0)
        end_time = int(fight.get("endTime") or 0)
        normalized.append(
            {
                "id": int(fight.get("id") or 0),
                "name": fight.get("name") or "Unknown Fight",
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": max(0, end_time - start_time),
                "kill": bool(fight.get("kill")),
                "boss_percentage": fight.get("bossPercentage"),
            }
        )
    return normalized


def select_fights(all_fights, fight_ids):
    if not fight_ids:
        return []

    fight_map = {}
    for fight in all_fights:
        fight_map[fight["id"]] = fight

    selected = []
    missing = []
    for fight_id in fight_ids:
        fight = fight_map.get(fight_id)
        if not fight:
            missing.append(fight_id)
            continue
        selected.append(fight)

    if missing:
        raise WCLCollectorError("以下 fight-id 在报告中不存在: %s" % ", ".join([str(item) for item in missing]))
    return selected


def split_range(start_time, end_time, window_ms, context):
    if end_time < start_time:
        raise WCLCollectorError("时间窗口非法: end_ms 不能小于 start_ms。")
    if end_time == start_time:
        end_time = start_time + 1

    windows = []
    cursor = int(start_time)
    window_index = 1
    while cursor < int(end_time):
        next_end = min(cursor + int(window_ms), int(end_time))
        item = {
            "window_index": window_index,
            "start_time": cursor,
            "end_time": next_end,
        }
        item.update(context)
        windows.append(item)
        cursor = next_end
        window_index += 1
    return windows


def build_windows(report_duration, selected_fights, start_ms, end_ms, window_ms):
    if selected_fights and (start_ms is not None or end_ms is not None):
        raise WCLCollectorError("不能同时使用 fight-id 和 start-ms/end-ms，请二选一。")

    if selected_fights:
        windows = []
        for fight in selected_fights:
            windows.extend(
                split_range(
                    fight["start_time"],
                    fight["end_time"],
                    window_ms,
                    {
                        "scope": "fight",
                        "fight_id": fight["id"],
                        "fight_name": fight["name"],
                    },
                )
            )
        return windows

    effective_start = 0 if start_ms is None else int(start_ms)
    effective_end = int(report_duration) if end_ms is None else int(end_ms)

    if effective_start < 0 or effective_end < 0:
        raise WCLCollectorError("start-ms 和 end-ms 不能为负数。")
    if effective_end > int(report_duration):
        raise WCLCollectorError(
            "end-ms 超出报告范围。当前报告时长为 %d ms。" % int(report_duration)
        )

    return split_range(
        effective_start,
        effective_end,
        window_ms,
        {"scope": "range", "fight_id": None, "fight_name": None},
    )


def fetch_events_for_windows(client, report_code, data_type, windows, max_pages_per_window):
    all_events = []
    warnings = []
    window_summaries = []
    total_pages = 0

    for window in windows:
        page_count = 0
        current_start = int(window["start_time"])
        final_end = int(window["end_time"])
        window_events = []
        partial = False

        while current_start < final_end:
            page_count += 1
            total_pages += 1
            if page_count > int(max_pages_per_window):
                partial = True
                warnings.append(
                    "窗口 %s 达到最大分页次数 %d，已提前停止。"
                    % (describe_window(window), int(max_pages_per_window))
                )
                break

            page = client.fetch_events_page(report_code, data_type, current_start, final_end)
            page_events = page.get("data") or []
            next_page_timestamp = page.get("nextPageTimestamp")
            window_events.extend(page_events)

            if next_page_timestamp in (None, ""):
                break

            try:
                next_page_timestamp = int(next_page_timestamp)
            except (TypeError, ValueError):
                partial = True
                warnings.append(
                    "窗口 %s 返回了无效的 nextPageTimestamp=%s。"
                    % (describe_window(window), next_page_timestamp)
                )
                break

            if next_page_timestamp <= current_start:
                partial = True
                warnings.append(
                    "窗口 %s 的 nextPageTimestamp 未前进，已停止以避免死循环。"
                    % describe_window(window)
                )
                break

            if next_page_timestamp >= final_end:
                break

            current_start = next_page_timestamp

        all_events.extend(window_events)
        window_summaries.append(
            {
                "scope": window.get("scope"),
                "fight_id": window.get("fight_id"),
                "fight_name": window.get("fight_name"),
                "window_index": window.get("window_index"),
                "start_time": window.get("start_time"),
                "end_time": window.get("end_time"),
                "page_count": page_count,
                "event_count": len(window_events),
                "partial": partial,
            }
        )

    return {
        "events": all_events,
        "warnings": warnings,
        "windows": window_summaries,
        "page_count": total_pages,
    }


def describe_window(window):
    if window.get("fight_id"):
        return "fight %s (%s) %s-%s" % (
            window.get("fight_id"),
            window.get("fight_name") or "Unknown",
            window.get("start_time"),
            window.get("end_time"),
        )
    return "range %s-%s" % (window.get("start_time"), window.get("end_time"))


def sanitize_filename_part(value):
    value = str(value or "unknown")
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "unknown"


def build_scope_label(fight_ids, start_ms, end_ms, metadata_only):
    if metadata_only:
        return "metadata"
    if fight_ids:
        return "fight-" + "-".join([str(item) for item in fight_ids])
    if start_ms is not None or end_ms is not None:
        start_label = "0" if start_ms is None else str(start_ms)
        end_label = "auto" if end_ms is None else str(end_ms)
        return "range-%s-%s" % (start_label, end_label)
    return "full-report"


def save_report(payload, report_code, data_type, fight_ids, start_ms, end_ms, output_dir):
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    filename = "report_%s_%s_%s.json" % (
        sanitize_filename_part(report_code),
        sanitize_filename_part(data_type.lower()),
        sanitize_filename_part(build_scope_label(fight_ids, start_ms, end_ms, payload["request"].get("metadata_only"))),
    )
    target_path = os.path.join(output_dir, filename)
    with open(target_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return target_path


def collect_report(
    client,
    report_code,
    data_type=DEFAULT_DATA_TYPE,
    fight_ids=None,
    start_ms=None,
    end_ms=None,
    window_ms=DEFAULT_WINDOW_MS,
    metadata_only=False,
    max_pages_per_window=DEFAULT_MAX_PAGES_PER_WINDOW,
):
    report_code = ensure_valid_report_code(report_code)
    data_type = ensure_valid_data_type(data_type)
    if int(window_ms) <= 0:
        raise WCLCollectorError("window-ms 必须大于 0。")
    if int(max_pages_per_window) <= 0:
        raise WCLCollectorError("max-pages-per-window 必须大于 0。")

    metadata = client.fetch_report_metadata(report_code)
    report_start_time = int(metadata.get("startTime") or 0)
    report_end_time = int(metadata.get("endTime") or 0)
    report_duration = max(0, report_end_time - report_start_time)

    all_fights = normalize_fights(metadata.get("fights") or [])
    selected_fights = select_fights(all_fights, fight_ids or [])
    windows = []
    fetch_result = {
        "events": [],
        "warnings": [],
        "windows": [],
        "page_count": 0,
    }

    if not metadata_only:
        windows = build_windows(report_duration, selected_fights, start_ms, end_ms, window_ms)
        fetch_result = fetch_events_for_windows(
            client,
            report_code,
            data_type,
            windows,
            max_pages_per_window,
        )

    payload = {
        "schema_version": 2,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "provider": "warcraftlogs-cn",
            "oauth_url": OAUTH_URL,
            "graphql_url": GRAPHQL_URL,
            "report_code": report_code,
        },
        "request": {
            "data_type": data_type,
            "fight_ids": fight_ids or [],
            "start_ms": start_ms,
            "end_ms": end_ms,
            "window_ms": int(window_ms),
            "metadata_only": bool(metadata_only),
            "max_pages_per_window": int(max_pages_per_window),
        },
        "report": {
            "start_time_unix_ms": report_start_time,
            "end_time_unix_ms": report_end_time,
            "duration_ms": report_duration,
            "fight_count": len(all_fights),
            "fights": all_fights,
            "selected_fights": selected_fights,
        },
        "event_fetch": {
            "window_count": len(windows),
            "page_count": fetch_result["page_count"],
            "event_count": len(fetch_result["events"]),
            "warnings": fetch_result["warnings"],
            "windows": fetch_result["windows"],
        },
        "events": fetch_result["events"],
    }
    return payload


def parse_args():
    parser = argparse.ArgumentParser(description="抓取 Warcraft Logs 中国区报告与事件数据")
    parser.add_argument("report_code", nargs="?", help="WCL 报告代码，例如 ABCdefG123")
    parser.add_argument(
        "--data-type",
        default=DEFAULT_DATA_TYPE,
        help="WCL events dataType，默认 Casts，可改为 DamageDone / DamageTaken / Deaths 等",
    )
    parser.add_argument(
        "--fight-id",
        action="append",
        default=[],
        help="要抓取的 fight id，可重复传入，也可写成逗号分隔，例如 --fight-id 3 --fight-id 4 或 --fight-id 3,4",
    )
    parser.add_argument("--start-ms", type=int, help="相对报告起点的开始毫秒")
    parser.add_argument("--end-ms", type=int, help="相对报告起点的结束毫秒")
    parser.add_argument(
        "--window-ms",
        type=int,
        default=DEFAULT_WINDOW_MS,
        help="按时间窗分段抓取的毫秒数，默认 600000 (10 分钟)",
    )
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="只抓取报告元数据和 fight 列表，不抓事件",
    )
    parser.add_argument(
        "--max-pages-per-window",
        type=int,
        default=DEFAULT_MAX_PAGES_PER_WINDOW,
        help="单个时间窗允许的最大分页次数，默认 100",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="网络超时时间（秒），默认 30",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="JSON 输出目录，默认 data/reports",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    report_code = args.report_code or prompt_input("请输入 WCL 报告代码: ").strip()

    try:
        report_code = ensure_valid_report_code(report_code)
        data_type = ensure_valid_data_type(args.data_type)
        fight_ids = parse_fight_ids(args.fight_id)
        client_id, client_secret = get_credentials()
        client = WCLClient(client_id, client_secret, timeout=args.timeout)

        print(">>> 正在连接 WCL 中国区服务器...")
        payload = collect_report(
            client=client,
            report_code=report_code,
            data_type=data_type,
            fight_ids=fight_ids,
            start_ms=args.start_ms,
            end_ms=args.end_ms,
            window_ms=args.window_ms,
            metadata_only=args.metadata_only,
            max_pages_per_window=args.max_pages_per_window,
        )
        saved_path = save_report(
            payload,
            report_code,
            data_type,
            fight_ids,
            args.start_ms,
            args.end_ms,
            args.output_dir,
        )
    except (requests.RequestException, ValueError, WCLCollectorError) as exc:
        print(">>> 处理失败: %s" % exc)
        return 1

    print(">>> 采集成功！原始数据已保存至: %s" % saved_path)
    print(">>> Fight 数量: %d" % payload["report"]["fight_count"])
    print(">>> 事件数量: %d" % payload["event_fetch"]["event_count"])
    if payload["event_fetch"]["warnings"]:
        print(">>> 注意：本次抓取包含 %d 条警告。" % len(payload["event_fetch"]["warnings"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
