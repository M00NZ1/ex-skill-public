#!/usr/bin/env python3
"""微信官方 ChatBackup 清点器。

只读扫描官方迁移备份目录，整理出当前可确认的元信息：
- 设备信息
- 备份包信息
- 媒体时间片范围
- 可直接使用性判断

不会尝试解密，也不会改动原始备份。
"""

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def extract_printable_strings(file_path: Path, min_length: int = 4) -> List[str]:
    """提取二进制文件中的可打印字符串。"""
    try:
        data = file_path.read_bytes()
    except OSError:
        return []

    # 用 latin-1 做一一映射，先把字节安全转成字符串，再提取可读片段。
    text = data.decode("latin-1", errors="ignore")
    # 允许常见路径字符和标识符字符，尽量从二进制里捞出可读信息。
    pattern = re.compile(rf"[A-Za-z0-9_./:\-\u0080-\uFFFF]{{{min_length},}}")
    results: List[str] = []
    for match in pattern.finditer(text):
        value = repair_mojibake(match.group(0).strip())
        if value:
            results.append(value)
    return results


def repair_mojibake(value: str) -> str:
    """尽量修复 latin-1 兜底读取导致的 UTF-8 乱码。"""
    try:
        repaired = value.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore").strip()
        if repaired:
            return repaired
    except Exception:
        pass
    return value


def format_ts_ms(value: str) -> str:
    """把毫秒时间戳格式化为本地时间字符串。"""
    try:
        ts = int(value) / 1000
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return value


def parse_media_chunk_name(file_name: str) -> Dict[str, str]:
    """解析媒体包名中的时间范围。"""
    match = re.match(r"(?P<start>\d+)-(?P<end>\d+)\.tar\.enc$", file_name)
    if not match:
        return {
            "start_ms": "",
            "end_ms": "",
            "start_time": "",
            "end_time": "",
        }

    start_ms = match.group("start")
    end_ms = match.group("end")
    return {
        "start_ms": start_ms,
        "end_ms": end_ms,
        "start_time": format_ts_ms(start_ms),
        "end_time": format_ts_ms(end_ms),
    }


def read_device_info(root: Path) -> Dict[str, str]:
    """读取顶层设备信息。"""
    device_file = root / ".wechat-deviceId"
    if not device_file.exists():
        return {}

    try:
        payload = json.loads(device_file.read_text(encoding="utf-8"))
    except Exception:
        return {}

    try:
        inner = json.loads(payload.get("data", "{}"))
    except Exception:
        inner = {}

    result = {}
    if payload.get("digest"):
        result["digest"] = payload["digest"]
    if inner.get("deviceId"):
        result["device_id"] = inner["deviceId"]
    if inner.get("accessMode"):
        result["access_mode"] = inner["accessMode"]
    return result


def summarize_package(package_dir: Path) -> Dict:
    """汇总单个备份包。"""
    files_dir = package_dir / "files" / "1"
    pkg_info_path = files_dir / "pkg_info.dat"
    backup_attr_path = package_dir / "backup.attr"
    tar_index_path = files_dir / "tar_index.dat"

    pkg_strings = extract_printable_strings(pkg_info_path)
    tar_index_strings = extract_printable_strings(tar_index_path)

    wxids = sorted({text for text in pkg_strings if text.startswith("wxid_")})
    device_models = sorted({text for text in pkg_strings if re.match(r"^[A-Za-z0-9_-]{3,}$", text) and "wxid_" not in text and "PREFIX" not in text and "/" not in text})

    media_chunks = []
    for file_path in sorted(files_dir.rglob("*.tar.enc")):
        if "Media" not in file_path.parts:
            continue

        chunk = {
            "relative_path": str(file_path.relative_to(package_dir)),
            "file_name": file_path.name,
            "size_bytes": file_path.stat().st_size,
        }
        chunk.update(parse_media_chunk_name(file_path.name))
        media_chunks.append(chunk)

    all_files = list(files_dir.rglob("*"))
    file_count = len([item for item in all_files if item.is_file()])
    dir_count = len([item for item in all_files if item.is_dir()])

    extensions: Dict[str, int] = {}
    for item in all_files:
        if not item.is_file():
            continue
        ext = item.suffix or "[no_ext]"
        extensions[ext] = extensions.get(ext, 0) + 1

    overall_start = next((item["start_time"] for item in media_chunks if item["start_time"]), "")
    overall_end = next((item["end_time"] for item in reversed(media_chunks) if item["end_time"]), "")

    return {
        "package_id": package_dir.name,
        "backup_attr_exists": backup_attr_path.exists(),
        "files_dir": str(files_dir),
        "file_count": file_count,
        "dir_count": dir_count,
        "extensions": extensions,
        "wxids": wxids,
        "pkg_info_strings": pkg_strings[:30],
        "tar_index_strings": tar_index_strings[:30],
        "device_models": device_models[:10],
        "media_chunk_count": len(media_chunks),
        "media_overall_start": overall_start,
        "media_overall_end": overall_end,
        "media_chunks": media_chunks,
        "direct_usable_chat_text": False,
        "direct_usable_media_files": False,
        "note": "检测到的是微信官方备份容器，仅能整理元信息与媒体时间片，无法直接解出聊天文本或媒体原文件。",
    }


def build_markdown(root: Path, device_info: Dict[str, str], packages: List[Dict]) -> str:
    """生成 Markdown 汇总报告。"""
    lines = [
        "# 微信官方 ChatBackup 整理报告",
        "",
        f"- 备份根目录：{root}",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 设备信息",
    ]

    if device_info:
        for key, value in device_info.items():
            lines.append(f"- {key}：{value}")
    else:
        lines.append("- [未读到设备信息]")

    lines.extend([
        "",
        "## 结论",
        "- 这是微信官方迁移备份，不是可直接导入的聊天文本。",
        "- 当前可直接整理出的只有：设备信息、wxid、媒体时间片范围、包结构。",
        "- 当前无法直接整理出的内容：聊天正文、图片原图、语音原文件、视频原文件。",
        "- 如果你要最终直接使用，仍然需要一份可读导出（txt/json/html）或可解开的第三方导出结果。",
        "",
    ])

    for index, package in enumerate(packages, 1):
        lines.extend([
            f"## 备份包 {index}",
            f"- package_id：{package['package_id']}",
            f"- 文件数：{package['file_count']}",
            f"- 子目录数：{package['dir_count']}",
            f"- wxid：{', '.join(package['wxids']) if package['wxids'] else '[未识别]'}",
            f"- 媒体时间片数量：{package['media_chunk_count']}",
            f"- 媒体时间范围：{package['media_overall_start'] or '[未知]'} ~ {package['media_overall_end'] or '[未知]'}",
            f"- 说明：{package['note']}",
            "",
            "### 扩展名分布",
        ])
        for ext, count in sorted(package["extensions"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {ext}：{count}")

        lines.extend([
            "",
            "### pkg_info 可读字段",
        ])
        if package["pkg_info_strings"]:
            for item in package["pkg_info_strings"]:
                lines.append(f"- {item}")
        else:
            lines.append("- [无]")

        lines.extend([
            "",
            "### 前 10 个媒体时间片",
        ])
        if package["media_chunks"]:
            for chunk in package["media_chunks"][:10]:
                lines.append(
                    f"- {chunk['file_name']} | {chunk['start_time'] or '[未知]'} -> {chunk['end_time'] or '[未知]'} | {chunk['size_bytes']} bytes"
                )
        else:
            lines.append("- [无]")

        lines.append("")

    return "\n".join(lines)


def write_outputs(output_dir: Path, root: Path, device_info: Dict[str, str], packages: List[Dict]):
    """写出整理结果。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "backup_root": str(root),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "device_info": device_info,
        "package_count": len(packages),
        "packages": packages,
    }

    (output_dir / "chatbackup_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with open(output_dir / "chatbackup_media_chunks.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "package_id",
                "relative_path",
                "file_name",
                "size_bytes",
                "start_ms",
                "end_ms",
                "start_time",
                "end_time",
            ],
        )
        writer.writeheader()
        for package in packages:
            for chunk in package["media_chunks"]:
                writer.writerow({
                    "package_id": package["package_id"],
                    **chunk,
                })

    (output_dir / "chatbackup_report.md").write_text(
        build_markdown(root, device_info, packages),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description="微信官方 ChatBackup 清点器")
    parser.add_argument("--backup-dir", required=True, help="ChatBackup 根目录")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    args = parser.parse_args()

    root = Path(args.backup_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not root.is_dir():
        raise SystemExit(f"错误：备份目录不存在 {root}")

    package_dirs = sorted([
        item for item in root.iterdir()
        if item.is_dir() and (item / "backup.attr").exists() and (item / "files").is_dir()
    ])

    device_info = read_device_info(root)
    packages = [summarize_package(package_dir) for package_dir in package_dirs]
    write_outputs(output_dir, root, device_info, packages)

    print(f"已完成整理：{output_dir}")


if __name__ == "__main__":
    main()
