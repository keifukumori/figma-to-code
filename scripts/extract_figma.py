#!/usr/bin/env python3
"""
Figma JSON Extractor
====================
大きなFigma JSONファイルからCSS生成に必要な情報を抽出し、
軽量なMarkdownファイルとして出力するスクリプト。

使用方法:
  python extract_figma.py <figma-data.json> [output.md]

出力:
  - extracted.md (デフォルト) または指定したファイル名

特徴:
  - figma_properties.json のホワイトリストを参照
  - 未知のプロパティは警告を出してホワイトリストに自動追加
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime


# ホワイトリストファイルのパス
SCRIPT_DIR = Path(__file__).parent
WHITELIST_FILE = SCRIPT_DIR / "figma_properties.json"

# CSS生成に不要なプロパティ（ブラックリスト）
BLACKLIST_PROPS = {
    "id", "pluginData", "sharedPluginData", "componentPropertyReferences",
    "componentPropertyDefinitions", "componentProperties", "overrides",
    "exportSettings", "preserveRatio", "layoutPositioning", "reactions",
    "transitionNodeID", "transitionDuration", "transitionEasing",
    "prototypeStartNodeID", "flowStartingPoints", "devicePresets",
    "children",  # 子要素は別途処理
    "document", "nodes",  # ルート構造
    "name", "type", "visible",  # 共通プロパティは別途処理
}


def load_whitelist():
    """ホワイトリストをロード"""
    if not WHITELIST_FILE.exists():
        print(f"⚠️ ホワイトリストファイルが見つかりません: {WHITELIST_FILE}")
        return {}

    with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_whitelist(whitelist):
    """ホワイトリストを保存"""
    whitelist["_meta"]["lastUpdated"] = datetime.now().strftime("%Y-%m-%d")
    with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
        json.dump(whitelist, f, indent=2, ensure_ascii=False)


def get_type_properties(whitelist, node_type):
    """ノードタイプのプロパティ一覧を取得（継承を解決）"""
    props = set()

    # 共通プロパティ
    if "common" in whitelist:
        props.update(whitelist["common"].get("properties", []))

    # タイプ固有のプロパティ
    if node_type in whitelist:
        type_config = whitelist[node_type]
        props.update(type_config.get("properties", []))

        # 継承
        if "inherits" in type_config:
            parent_type = type_config["inherits"]
            if parent_type in whitelist:
                props.update(whitelist[parent_type].get("properties", []))

    return props


def detect_unknown_properties(node, node_type, whitelist, unknown_props):
    """未知のプロパティを検出"""
    known_props = get_type_properties(whitelist, node_type)

    for key in node.keys():
        if key in BLACKLIST_PROPS:
            continue
        if key not in known_props:
            if node_type not in unknown_props:
                unknown_props[node_type] = set()
            unknown_props[node_type].add(key)


def add_unknown_to_whitelist(whitelist, unknown_props):
    """未知のプロパティをホワイトリストに追加"""
    added = []

    for node_type, props in unknown_props.items():
        if node_type not in whitelist:
            whitelist[node_type] = {
                "description": f"自動追加: {node_type}",
                "properties": []
            }

        existing = set(whitelist[node_type].get("properties", []))
        new_props = props - existing

        if new_props:
            whitelist[node_type]["properties"] = list(existing | new_props)
            for prop in new_props:
                added.append(f"{node_type}.{prop}")

    return added


# 特殊な変換処理が必要なプロパティ
# key: プロパティ名, value: 変換関数名（文字列）または "raw"（そのまま出力）
SPECIAL_CONVERTERS = {
    "fills": "extract_color",
    "strokes": "extract_stroke_color",
    "effects": "extract_effects",
}

# Markdown出力時にスキップするプロパティ（内部処理用や冗長なもの）
SKIP_IN_OUTPUT = {
    "path",  # 内部パス情報（JSONのpathと被る）
}

# 基本プロパティ（常に最初に出力）
BASE_PROPERTIES = ["name", "width", "height"]


def rgb_to_css(r, g, b, a=1):
    """Figmaの0-1形式をCSS rgb()形式に変換"""
    r_int = round(r * 255)
    g_int = round(g * 255)
    b_int = round(b * 255)
    if a < 1:
        return f"rgba({r_int}, {g_int}, {b_int}, {a:.2f})"
    return f"rgb({r_int}, {g_int}, {b_int})"


def extract_color(fills):
    """fills配列から色を抽出"""
    if not fills:
        return None
    for fill in fills:
        if fill.get("visible", True) and fill.get("type") == "SOLID":
            color = fill.get("color", {})
            r = color.get("r", 0)
            g = color.get("g", 0)
            b = color.get("b", 0)
            a = fill.get("opacity", 1)
            return rgb_to_css(r, g, b, a)
        elif fill.get("visible", True) and "GRADIENT" in fill.get("type", ""):
            stops = fill.get("gradientStops", [])
            if stops:
                colors = []
                for stop in stops:
                    c = stop.get("color", {})
                    colors.append(rgb_to_css(c.get("r", 0), c.get("g", 0), c.get("b", 0)))
                return f"gradient({' → '.join(colors)})"
    return None


def extract_stroke_color(strokes):
    """strokes配列から色を抽出"""
    if not strokes:
        return None
    for stroke in strokes:
        if stroke.get("visible", True) and stroke.get("type") == "SOLID":
            color = stroke.get("color", {})
            r = color.get("r", 0)
            g = color.get("g", 0)
            b = color.get("b", 0)
            return rgb_to_css(r, g, b)
    return None


def extract_effects(effects):
    """effects配列からCSS用の効果を抽出"""
    if not effects:
        return None
    result = []
    for effect in effects:
        if not effect.get("visible", True):
            continue
        effect_type = effect.get("type", "")
        if effect_type == "DROP_SHADOW":
            color = effect.get("color", {})
            r = color.get("r", 0)
            g = color.get("g", 0)
            b = color.get("b", 0)
            a = color.get("a", 1)
            offset = effect.get("offset", {})
            x = offset.get("x", 0)
            y = offset.get("y", 0)
            radius = effect.get("radius", 0)
            spread = effect.get("spread", 0)
            result.append(f"drop-shadow({x}px {y}px {radius}px {spread}px {rgb_to_css(r, g, b, a)})")
        elif effect_type == "INNER_SHADOW":
            color = effect.get("color", {})
            r = color.get("r", 0)
            g = color.get("g", 0)
            b = color.get("b", 0)
            a = color.get("a", 1)
            offset = effect.get("offset", {})
            x = offset.get("x", 0)
            y = offset.get("y", 0)
            radius = effect.get("radius", 0)
            result.append(f"inner-shadow({x}px {y}px {radius}px {rgb_to_css(r, g, b, a)})")
        elif effect_type == "LAYER_BLUR":
            radius = effect.get("radius", 0)
            result.append(f"blur({radius}px)")
        elif effect_type == "BACKGROUND_BLUR":
            radius = effect.get("radius", 0)
            result.append(f"backdrop-blur({radius}px)")
    return ", ".join(result) if result else None


def get_font_style(node):
    """rangeAllFontNamesからフォントスタイルを抽出"""
    range_fonts = node.get("rangeAllFontNames", [])
    if range_fonts and len(range_fonts) > 0:
        first_range = range_fonts[0]
        if first_range and len(first_range) > 0:
            font_info = first_range[0]
            family = font_info.get("family", "")
            style = font_info.get("style", "")
            return family, style
    return None, None


def style_to_weight(style):
    """フォントスタイルをfontWeight数値に変換"""
    if not style:
        return None
    style_lower = style.lower()
    weight_map = {
        "thin": 100,
        "extralight": 200,
        "light": 300,
        "regular": 400,
        "medium": 500,
        "semibold": 600,
        "bold": 700,
        "extrabold": 800,
        "black": 900,
    }
    for key, value in weight_map.items():
        if key in style_lower:
            return value
    return 400  # デフォルト


def get_dimensions(node):
    """ノードのサイズと位置を取得（absoluteBoundingBoxまたは直接プロパティ）"""
    bbox = node.get("absoluteBoundingBox", {})
    return {
        "width": bbox.get("width") or node.get("width"),
        "height": bbox.get("height") or node.get("height"),
        "x": bbox.get("x") or node.get("x"),
        "y": bbox.get("y") or node.get("y"),
    }


def format_value_for_markdown(value):
    """値をMarkdown出力用にフォーマット"""
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        # パイプ文字と改行をエスケープ
        return value.replace("|", "\\|").replace("\n", " ")
    if isinstance(value, list):
        if len(value) == 0:
            return None
        # リストはJSON形式で出力（長い場合は切り詰め）
        json_str = json.dumps(value, ensure_ascii=False)
        if len(json_str) > 100:
            return json_str[:100] + "..."
        return json_str
    if isinstance(value, dict):
        # 辞書はJSON形式で出力（長い場合は切り詰め）
        json_str = json.dumps(value, ensure_ascii=False)
        if len(json_str) > 100:
            return json_str[:100] + "..."
        return json_str
    return str(value)


def extract_node_properties_dynamic(node, node_type, whitelist, current_path):
    """
    ホワイトリストに基づいてノードのプロパティを動的に抽出
    JSONに存在するプロパティはすべて抽出される
    """
    dims = get_dimensions(node)

    # 基本情報
    info = {
        "name": node.get("name", "Unknown"),
        "path": current_path,
        "width": dims.get("width"),
        "height": dims.get("height"),
    }

    # ホワイトリストのプロパティを取得
    whitelist_props = get_type_properties(whitelist, node_type)

    # JSONに存在するすべてのプロパティを走査
    for key in node.keys():
        # ブラックリストはスキップ
        if key in BLACKLIST_PROPS:
            continue
        # 既に処理済みの基本プロパティはスキップ
        if key in ["name", "absoluteBoundingBox"]:
            continue

        value = node.get(key)
        if value is None:
            continue

        # 特殊変換が必要なプロパティ
        if key in SPECIAL_CONVERTERS:
            converter_name = SPECIAL_CONVERTERS[key]
            if converter_name == "extract_color":
                converted = extract_color(value)
            elif converter_name == "extract_stroke_color":
                converted = extract_stroke_color(value)
            elif converter_name == "extract_effects":
                converted = extract_effects(value)
            else:
                converted = value

            # 変換後のキー名を調整
            if key == "fills":
                info["fill"] = converted
            elif key == "strokes":
                info["stroke"] = converted
            else:
                info[key] = converted
        else:
            # そのまま格納
            info[key] = value

    return info


def traverse_nodes(node, path="", results=None, warnings=None, whitelist=None, unknown_props=None):
    """ノードを再帰的に走査して情報を抽出"""
    if results is None:
        results = {
            "texts": [],
            "frames": [],
            "rectangles": [],
            "vectors": [],
            "lines": [],
            "ellipses": [],
        }
    if warnings is None:
        warnings = []
    if unknown_props is None:
        unknown_props = {}

    node_type = node.get("type", "")
    node_name = node.get("name", "Unknown")
    visible = node.get("visible", True)
    current_path = f"{path}/{node_name}" if path else node_name

    # 非表示要素はスキップ
    if not visible:
        return results, warnings, unknown_props

    # 未知プロパティの検出
    if whitelist:
        detect_unknown_properties(node, node_type, whitelist, unknown_props)

    # テキスト要素
    if node_type == "TEXT":
        font_family, font_style = get_font_style(node)
        dims = get_dimensions(node)

        # styleオブジェクトからテキストスタイル情報を取得
        style = node.get("style", {})

        # fontWeightはstyleオブジェクトから直接取得、なければスタイル名から推測
        font_weight = style.get("fontWeight") or style_to_weight(font_style)

        # fontFamilyもstyleオブジェクトから取得可能
        if not font_family:
            font_family = style.get("fontFamily")

        text_info = {
            "name": node_name,
            "path": current_path,
            "characters": node.get("characters", ""),
            "fontSize": style.get("fontSize") or node.get("fontSize"),
            "fontWeight": font_weight,
            "fontFamily": font_family,
            "lineHeight": style.get("lineHeightPx") or node.get("lineHeightPx") or dims.get("height"),
            "letterSpacing": style.get("letterSpacing") or node.get("letterSpacing"),
            "textAlign": style.get("textAlignHorizontal") or node.get("textAlignHorizontal"),
            "color": extract_color(node.get("fills", [])),
            "opacity": node.get("opacity", 1),
            "width": dims.get("width"),
            "height": dims.get("height"),
        }

        # 警告チェック
        if text_info["fontSize"] is None:
            warnings.append(f"⚠️ fontSize未取得: {node_name} (path: {current_path})")

        results["texts"].append(text_info)

    # フレーム/コンポーネント
    elif node_type in ["FRAME", "COMPONENT", "INSTANCE", "GROUP"]:
        dims = get_dimensions(node)
        frame_info = {
            "name": node_name,
            "path": current_path,
            "type": node_type,
            "width": dims.get("width"),
            "height": dims.get("height"),
            "x": dims.get("x"),
            "y": dims.get("y"),
            "paddingTop": node.get("paddingTop"),
            "paddingRight": node.get("paddingRight"),
            "paddingBottom": node.get("paddingBottom"),
            "paddingLeft": node.get("paddingLeft"),
            "itemSpacing": node.get("itemSpacing"),
            "counterAxisSpacing": node.get("counterAxisSpacing"),
            "cornerRadius": node.get("cornerRadius"),
            "backgroundColor": extract_color(node.get("fills", [])),
            "borderColor": extract_stroke_color(node.get("strokes", [])),
            "strokeWeight": node.get("strokeWeight"),
            "layoutMode": node.get("layoutMode"),
            "overflowDirection": node.get("overflowDirection"),
            "primaryAxisAlignItems": node.get("primaryAxisAlignItems"),
            "counterAxisAlignItems": node.get("counterAxisAlignItems"),
            "opacity": node.get("opacity", 1),
            "effects": extract_effects(node.get("effects", [])),
        }
        results["frames"].append(frame_info)

    # 矩形（動的プロパティ抽出）
    elif node_type == "RECTANGLE":
        rect_info = extract_node_properties_dynamic(node, node_type, whitelist, current_path)
        results["rectangles"].append(rect_info)

    # ベクター/アイコン（動的プロパティ抽出）
    elif node_type == "VECTOR":
        vector_info = extract_node_properties_dynamic(node, node_type, whitelist, current_path)
        results["vectors"].append(vector_info)

    # 線（動的プロパティ抽出）
    elif node_type == "LINE":
        line_info = extract_node_properties_dynamic(node, node_type, whitelist, current_path)
        results["lines"].append(line_info)

    # 楕円/円（動的プロパティ抽出）
    elif node_type == "ELLIPSE":
        ellipse_info = extract_node_properties_dynamic(node, node_type, whitelist, current_path)
        results["ellipses"].append(ellipse_info)

    # その他のノードタイプも動的に処理（BOOLEAN_OPERATION, STAR, REGULAR_POLYGON等）
    elif node_type in ["BOOLEAN_OPERATION", "STAR", "REGULAR_POLYGON"]:
        other_info = extract_node_properties_dynamic(node, node_type, whitelist, current_path)
        # vectorsに追加（形状系として扱う）
        results["vectors"].append(other_info)

    # 子要素を再帰処理
    children = node.get("children", [])
    for child in children:
        traverse_nodes(child, current_path, results, warnings, whitelist, unknown_props)

    return results, warnings, unknown_props


def generate_dynamic_table(title, items):
    """
    アイテムのリストから動的にMarkdownテーブルを生成
    各アイテムに存在するすべてのプロパティをカラムとして出力
    """
    if not items:
        return []

    lines = []
    lines.append(f"## {title}")
    lines.append("")

    # 全アイテムから存在するキーを収集（順序を保持）
    all_keys = []
    seen_keys = set()

    # 優先的に表示するキー（順序指定）
    priority_keys = ["name", "width", "height", "fill", "stroke", "strokeWeight",
                     "cornerRadius", "strokeCap", "strokeJoin", "opacity"]

    # まず優先キーを追加
    for key in priority_keys:
        for item in items:
            if key in item and key not in seen_keys:
                all_keys.append(key)
                seen_keys.add(key)
                break

    # 残りのキーを追加
    for item in items:
        for key in item.keys():
            if key not in seen_keys and key not in SKIP_IN_OUTPUT:
                all_keys.append(key)
                seen_keys.add(key)

    # ヘッダー行
    header = "| " + " | ".join(all_keys) + " |"
    separator = "|" + "|".join(["------" for _ in all_keys]) + "|"
    lines.append(header)
    lines.append(separator)

    # データ行
    for item in items:
        row_values = []
        for key in all_keys:
            value = item.get(key)
            formatted = format_value_for_markdown(value)
            if formatted is None:
                row_values.append("-")
            else:
                row_values.append(str(formatted))
        lines.append("| " + " | ".join(row_values) + " |")

    lines.append("")
    return lines


def generate_markdown(results, warnings, input_file, unknown_props=None, added_props=None):
    """抽出結果をMarkdown形式で出力"""
    lines = []

    # ヘッダー
    lines.append(f"# Figma Data Extract")
    lines.append(f"")
    lines.append(f"Source: `{input_file}`")
    lines.append(f"")

    # 警告セクション
    if warnings or unknown_props or added_props:
        lines.append("## ⚠️ Warnings")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        if added_props:
            lines.append(f"- 🆕 ホワイトリストに追加されたプロパティ: {', '.join(added_props)}")
        lines.append("")

    # サマリー
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Type | Count |")
    lines.append(f"|------|-------|")
    lines.append(f"| Texts | {len(results['texts'])} |")
    lines.append(f"| Frames/Components | {len(results['frames'])} |")
    lines.append(f"| Rectangles | {len(results['rectangles'])} |")
    lines.append(f"| Vectors | {len(results['vectors'])} |")
    lines.append(f"| Lines | {len(results['lines'])} |")
    lines.append(f"| Ellipses | {len(results['ellipses'])} |")
    lines.append("")

    # テキスト要素
    if results["texts"]:
        lines.append("## Texts")
        lines.append("")
        lines.append("| Name | Characters | fontSize | fontWeight | lineHeight | letterSpacing | textAlign | opacity | color |")
        lines.append("|------|------------|----------|------------|------------|---------------|-----------|---------|-------|")
        for t in results["texts"]:
            chars = t["characters"][:30] + "..." if len(t["characters"]) > 30 else t["characters"]
            chars = chars.replace("|", "\\|").replace("\n", " ")
            letter_spacing = t.get('letterSpacing', '-')
            text_align = t.get('textAlign', '-')
            opacity = t.get('opacity', 1)
            opacity_str = str(opacity) if opacity != 1 else "-"
            lines.append(f"| {t['name']} | {chars} | {t['fontSize']} | {t['fontWeight']} | {t['lineHeight']} | {letter_spacing} | {text_align} | {opacity_str} | {t['color']} |")
        lines.append("")

    # フレーム/コンポーネント
    if results["frames"]:
        lines.append("## Frames & Components")
        lines.append("")
        lines.append("| Name | Type | Width | Height | Padding (T/R/B/L) | Gap | Corner | BG Color | Layout | Overflow | Opacity |")
        lines.append("|------|------|-------|--------|-------------------|-----|--------|----------|--------|----------|---------|")
        for f in results["frames"]:
            padding = f"{f['paddingTop']}/{f['paddingRight']}/{f['paddingBottom']}/{f['paddingLeft']}"
            if padding == "None/None/None/None":
                padding = "-"
            opacity = f.get('opacity', 1)
            opacity_str = str(opacity) if opacity != 1 else "-"
            layout = f.get('layoutMode', '-') or "-"
            overflow = f.get('overflowDirection', '-') or "-"
            lines.append(f"| {f['name']} | {f['type']} | {f['width']} | {f['height']} | {padding} | {f['itemSpacing']} | {f['cornerRadius']} | {f['backgroundColor']} | {layout} | {overflow} | {opacity_str} |")
        lines.append("")

    # 矩形（動的カラム生成）
    if results["rectangles"]:
        lines.extend(generate_dynamic_table("Rectangles", results["rectangles"]))

    # ベクター（動的カラム生成）
    if results["vectors"]:
        lines.extend(generate_dynamic_table("Vectors (Icons/Lines)", results["vectors"]))

    # 線（動的カラム生成）
    if results["lines"]:
        lines.extend(generate_dynamic_table("Lines", results["lines"]))

    # 楕円（動的カラム生成）
    if results["ellipses"]:
        lines.extend(generate_dynamic_table("Ellipses", results["ellipses"]))

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_figma.py <figma-data.json> [output.md]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    # デフォルト出力先は入力ファイルと同じディレクトリ
    if output_file is None:
        input_path = Path(input_file)
        output_file = input_path.parent / "extracted.md"

    # ホワイトリスト読み込み
    print(f"Loading whitelist: {WHITELIST_FILE}")
    whitelist = load_whitelist()

    # JSON読み込み
    print(f"Reading: {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ルートノードを探す
    root = data
    if "document" in data:
        root = data["document"]
    elif "nodes" in data:
        # Figma API形式: nodes > {nodeId} > document
        for node_id, node_data in data["nodes"].items():
            if "document" in node_data:
                root = node_data["document"]
                break
    elif "children" in data:
        pass  # rootはそのまま

    # 抽出実行
    print("Extracting...")
    results, warnings, unknown_props = traverse_nodes(root, whitelist=whitelist)

    # 未知プロパティの処理
    added_props = []
    if unknown_props:
        print(f"\n🆕 未知のプロパティを検出:")
        for node_type, props in unknown_props.items():
            for prop in props:
                print(f"   {node_type}.{prop}")

        # ホワイトリストに追加
        added_props = add_unknown_to_whitelist(whitelist, unknown_props)
        if added_props:
            save_whitelist(whitelist)
            print(f"\n✅ ホワイトリストに追加しました: {', '.join(added_props)}")

    # Markdown生成
    markdown = generate_markdown(results, warnings, input_file, unknown_props, added_props)

    # 出力
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)

    # 統計表示
    print(f"\n✅ Output: {output_file}")
    print(f"   Texts: {len(results['texts'])}")
    print(f"   Frames: {len(results['frames'])}")
    print(f"   Rectangles: {len(results['rectangles'])}")
    print(f"   Vectors: {len(results['vectors'])}")
    print(f"   Lines: {len(results['lines'])}")
    print(f"   Ellipses: {len(results['ellipses'])}")

    if warnings:
        print(f"\n⚠️ Warnings: {len(warnings)}")
        for w in warnings:
            print(f"   {w}")
    else:
        print(f"\n✅ No warnings")


if __name__ == "__main__":
    main()
