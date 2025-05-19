import argparse
import logging
import os
import subprocess
from pathlib import Path

import polib

logger = logging.getLogger(__name__)


def find_py_files(base_dir: str) -> str:
    """查找所有 .py 文件.

    Args:
        base_dir: 项目根目录路径

    Returns:
        list[str]: 所有 .py 文件的路径列表

    """
    try:
        base_path = Path(base_dir)
        if not Path.exists(base_path):
            msg = f"目录 {base_dir} 不存在"
            raise FileNotFoundError(msg)  # noqa: TRY301

        py_files = [str(file) for file in base_path.rglob("*.py")]
        if not py_files:
            msg = f"在 {base_dir} 中未找到任何.py 文件"
            raise FileNotFoundError(msg)  # noqa: TRY301
        logger.info("找到 %s 个 .py 文件", len(py_files))
    except Exception as e:
        msg = f"在 {base_dir} 中未找到任何.py 文件"
        raise FileNotFoundError(msg) from e
    return py_files


def extract_messages(py_files: str, output_dir: str, domain: str = "messages") -> str:
    """使用 xgettext 提取翻译字符串."""
    if not py_files:
        msg = "没有.py 文件可供提取"
        raise Exception(msg)  # noqa: TRY002

    try:
        Path.mkdir(output_dir, exist_ok=True)
        pot_file = str(Path(output_dir) / f"{domain}.pot")

        cmd = [
            "xgettext",
            "--from-code=UTF-8",
            "-L",
            "Python",
            "-o",
            pot_file,
            "--package-name=moonshot_tools",
            "--msgid-bugs-address=your@email.com",
            "--add-comments=TRANSLATORS:",
            "--keyword=_",
            *py_files,
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)  # noqa: S603
        logger.info("已生成 POT 文件: %s", pot_file)
    except subprocess.CalledProcessError as e:
        msg = f"xgettext 执行失败: {e}"
        raise Exception(msg) from e  # noqa: TRY002
    except Exception as e:
        msg = f"提取翻译字符串时出错: {e}"
        raise Exception(msg) from e  # noqa: TRY002
    return pot_file


def create_po_files(pot_file: str, locale_dir: str, languages: str) -> str:
    """从 POT 文件创建新的 PO 文件.

    Args:
        pot_file: POT 文件路径
        locale_dir: locale 目录路径
        languages: 语言代码列表,例如 ['zh_CN', 'en_US']

    """
    try:
        for lang in languages:
            # 创建语言目录
            lang_dir = Path(locale_dir) / lang / "LC_MESSAGES"
            lang_dir.mkdir(parents=True, exist_ok=True)

            # 生成 PO 文件
            po_file = Path(locale_dir) / lang / "LC_MESSAGES" / "messages.po"
            if not Path.exists(po_file):
                cmd = [
                    "msginit",
                    "--input=" + pot_file,
                    "--locale=" + lang,
                    "--output-file=" + po_file,
                    "--no-translator",
                ]
                # 移除 text=True,只保留 capture_output=True
                # 验证命令参数是否安全
                if not all(isinstance(arg, str) for arg in cmd):
                    msg = "命令参数必须都是字符串类型"
                    raise ValueError(msg)  # noqa: TRY301
                subprocess.run(cmd, check=True, capture_output=True, text=True)  # noqa: S603
                logger.info("已为语言 {%s} 创建新的 PO 文件: {%s}", lang, po_file)
            else:
                logger.warning("PO 文件已存在: %s", po_file)
    except subprocess.CalledProcessError as e:
        # 使用 errors='replace' 来处理无法解码的字符
        stderr = e.stderr.decode("utf-8", errors="replace")
        msg = f"msginit 执行失败: {stderr}"
        raise Exception(msg) from e  # noqa: TRY002
    except Exception as e:
        msg = f"创建 PO 文件时出错: {e}"
        raise Exception(msg) from e  # noqa: TRY002


def merge_po_files(pot_file: str, locale_dir: str) -> None:  # noqa: C901
    """使用 polib 合并 .pot 和现有 .po 文件,保留已有翻译."""
    try:
        # 加载新生成的 .pot 文件
        pot = polib.pofile(pot_file)

        locale_path = Path(locale_dir)
        po_files = list(locale_path.rglob("*.po"))

        if not po_files:
            logger.warning("在 %s 中未找到 .po 文件,跳过合并", locale_dir)
            return

        for po_file_path in po_files:
            if Path.exists(po_file_path):
                # 加载现有的 .po 文件
                po = polib.pofile(str(po_file_path), encoding="utf-8")
                logger.info("正在合并现有 PO 文件: %s", po_file_path)
            else:
                # 如果 .po 文件不存在,创建一个新的
                po = polib.POFile()
                po.metadata = pot.metadata.copy()  # 复制 .pot 的元信息
                logger.info("创建新的 PO 文件: %s", po_file_path)

            # 合并逻辑:保留已有翻译,添加新条目,标记废弃条目
            existing_entries = {entry.msgid: entry for entry in po}
            for pot_entry in pot:
                if pot_entry.msgid in existing_entries:
                    # 如果已有翻译,保留它
                    existing_entry = existing_entries[pot_entry.msgid]
                    if existing_entry.msgstr:
                        pot_entry.msgstr = existing_entry.msgstr
                # 将新条目添加到 .po 文件(如果之前不存在)
                if pot_entry.msgid not in existing_entries:
                    po.append(pot_entry)

            # 标记废弃条目(在 .po 中存在但 .pot 中已删除)
            for msgid, entry in existing_entries.items():
                if msgid not in {e.msgid for e in pot}:
                    entry.obsolete = True  # 标记为废弃

            # 保存更新后的 .po 文件
            po.save(str(po_file_path))
            logger.info("已更新 PO 文件: %s", po_file_path)

    except Exception as e:
        msg = f"合并 .po 文件时出错: {e}"
        raise Exception(msg) from e  # noqa: TRY002


def compile_po_files(locale_dir: str) -> None:
    """编译所有 .po 文件为 .mo 文件."""
    try:
        locale_path = Path(locale_dir)
        if not Path.exists(locale_path):
            msg = f"locale 目录 {locale_dir} 不存在,跳过编译"
            raise FileNotFoundError(msg)  # noqa: TRY301

        po_files = list(locale_path.rglob("*.po"))
        if not po_files:
            msg = f"在 {locale_dir} 中未找到 .po 文件"
            raise FileNotFoundError(msg)  # noqa: TRY301

        for po_file in po_files:
            # 直接使用 po 文件所在的目录
            mo_dir = po_file.parent
            mo_file = mo_dir / (po_file.stem + ".mo")

            Path.mkdir(mo_dir, exist_ok=True)

            cmd = ["msgfmt", "-o", str(mo_file), str(po_file)]
            subprocess.run(cmd, check=True, capture_output=True, text=True)  # noqa: S603
            logger.info("已生成 MO 文件: %s", mo_file)
    except subprocess.CalledProcessError as e:
        msg = f"msgfmt 执行失败: {e}"
        raise Exception(msg) from e  # noqa: TRY002
    except Exception as e:
        msg = f"编译.po 文件时出错: {e}"
        raise Exception(msg) from e  # noqa: TRY002


def main() -> None:
    parser = argparse.ArgumentParser(description="国际化工具：提取、更新和编译翻译文件")
    parser.add_argument(
        "--base-dir",
        default=os.getenv("MOONSHOT_SRC_DIR", str(Path(__file__).parent.parent)),
        help="项目源代码根目录路径，默认为当前脚本的上级目录",
    )
    parser.add_argument(
        "--languages",
        default="zh_CN,en_US",
        help="需要支持的语言代码列表,用逗号分隔,例如:zh_CN,en_US",
    )

    args = parser.parse_args()
    base_dir = args.base_dir
    locale_dir = Path(base_dir) / "locale"
    languages = args.languages.split(",")
    # 1. 查找所有 .py 文件
    py_files = find_py_files(base_dir)

    # 2. 提取翻译字符串
    pot_file = extract_messages(py_files, locale_dir)

    # 3. 创建新的 PO 文件(如果不存在)
    create_po_files(pot_file, locale_dir, languages)

    # 4. 合并 .pot 和现有 .po 文件
    merge_po_files(pot_file, locale_dir)

    # 5. 编译 .po 文件为 .mo 文件
    compile_po_files(locale_dir)
    logger.info("翻译文件处理流程完成")


if __name__ == "__main__":
    main()
