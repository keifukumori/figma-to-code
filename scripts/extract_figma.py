#!/usr/bin/env python3
"""
Figma JSON Extractor (Phase 4実装版 - 重なり検出対応)
======================================
Phase 1-4で追加された機能:
1. componentProperties の抽出(バリアント情報)
2. rectangleCornerRadii の個別角丸抽出
3. lineHeight の単位情報(PIXELS/PERCENT)
4. 親子関係(parent_id, depth)の記録
5. Auto Layout None問題の調査・修正
6. overflowScrolling の追加(Phase 2)
7. SVGパスのハッシュ値(Phase 3)
8. exportSettings の画像情報(Phase 3)
9. **絶対座標(AbsoluteX/Y)の全要素記録(Phase 4)**
10. **layoutPositioning の追加(Phase 4)**
11. **要素の重なり検出と推奨CSS提案(Phase 4)**
"""

import json
import sys
import os
import hashlib
from pathlib import Path
from datetime import datetime


SCRIPT_DIR = Path(__file__).parent
WHITELIST_FILE = SCRIPT_DIR / "figma_properties.json"

BLACKLIST_PROPS = {
    "id", "pluginData", "sharedPluginData", "componentPropertyReferences",
    "componentPropertyDefinitions",
    "preserveRatio", "reactions",
    "transitionNodeID", "transitionDuration", "transitionEasing",
    "prototypeStartNodeID", "flowStartingPoints", "devicePresets",
    "children",
    "document", "nodes",
    "name", "type", "visible",
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
    """ノードタイプのプロパティ一覧を取得(継承を解決)"""
    props = set()

    if "common" in whitelist:
        props.update(whitelist["common"].get("properties", []))

    if node_type in whitelist:
        type_config = whitelist[node_type]
        props.update(type_config.get("properties", []))

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


SPECIAL_CONVERTERS = {
    "fills": "extract_color",
    "strokes": "extract_stroke_color",
    "effects": "extract_effects",
}

SKIP_IN_OUTPUT = {
    "path",
}

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


def extract_line_height_with_unit(node):
    """lineHeight の値と単位を抽出"""
    style = node.get("style", {})
    
    line_height_obj = style.get("lineHeight") or node.get("lineHeight")
    
    if isinstance(line_height_obj, dict):
        value = line_height_obj.get("value")
        unit = line_height_obj.get("unit", "PIXELS")
        if value is not None:
            return value, unit
    
    line_height_px = style.get("lineHeightPx") or node.get("lineHeightPx")
    if line_height_px is not None:
        return line_height_px, "PIXELS"
    
    line_height_percent = style.get("lineHeightPercentFontSize") or node.get("lineHeightPercentFontSize")
    if line_height_percent is not None:
        return line_height_percent, "PERCENT"
    
    return None, None


def extract_component_properties(node):
    """インスタンスの componentProperties を抽出"""
    comp_props = node.get("componentProperties", {})
    if not comp_props:
        return None
    
    result = []
    for key, prop_data in comp_props.items():
        value = prop_data.get("value")
        if value is not None:
            result.append(f"{key}={value}")
    
    return " | ".join(result) if result else None


def extract_overrides(node):
    """インスタンスの overrides を抽出"""
    overrides = node.get("overrides")
    if not overrides or not isinstance(overrides, list):
        return None
    
    override_info = []
    for override in overrides:
        override_id = override.get("id")
        overridden_fields = override.get("overriddenFields", [])
        if overridden_fields:
            override_info.append(f"{override_id}:{','.join(overridden_fields)}")
    
    return " | ".join(override_info) if override_info else None


def extract_svg_hash(node):
    """ベクターノードからSVGパスのハッシュ値を生成"""
    fill_geometry = node.get("fillGeometry")
    if fill_geometry:
        try:
            path_str = json.dumps(fill_geometry, sort_keys=True)
            path_hash = hashlib.md5(path_str.encode()).hexdigest()[:8]
            return path_hash
        except:
            return None
    
    vector_network = node.get("vectorNetwork")
    if vector_network:
        try:
            path_str = json.dumps(vector_network, sort_keys=True)
            path_hash = hashlib.md5(path_str.encode()).hexdigest()[:8]
            return path_hash
        except:
            return None
    
    return None


def extract_export_info(node):
    """exportSettings から画像情報を抽出"""
    export_settings = node.get("exportSettings")
    if not export_settings or not isinstance(export_settings, list):
        return None
    
    export_info = []
    for setting in export_settings:
        format_type = setting.get("format", "PNG")
        suffix = setting.get("suffix", "")
        constraint = setting.get("constraint", {})
        constraint_type = constraint.get("type", "SCALE")
        constraint_value = constraint.get("value", 1)
        
        info_str = f"{format_type}"
        if suffix:
            info_str += f"@{suffix}"
        if constraint_type == "SCALE" and constraint_value != 1:
            info_str += f" {constraint_value}x"
        elif constraint_type in ["WIDTH", "HEIGHT"]:
            info_str += f" {constraint_type}:{constraint_value}"
        
        export_info.append(info_str)
    
    return " | ".join(export_info) if export_info else None


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
    return 400


def get_dimensions(node):
    """ノードのサイズと位置を取得"""
    bbox = node.get("absoluteBoundingBox") or node.get("absoluteRenderBounds") or {}
    return {
        "width": bbox.get("width") or node.get("width"),
        "height": bbox.get("height") or node.get("height"),
        "x": bbox.get("x") or node.get("x"),
        "y": bbox.get("y") or node.get("y"),
    }


def get_absolute_position(node):
    """Phase 4: 絶対座標を取得"""
    # absoluteBoundingBox を優先
    abs_bounds = node.get("absoluteBoundingBox")
    if abs_bounds:
        return abs_bounds.get("x"), abs_bounds.get("y")
    
    # フォールバック: absoluteRenderBounds
    abs_render = node.get("absoluteRenderBounds")
    if abs_render:
        return abs_render.get("x"), abs_render.get("y")
    
    return None, None


def determine_layout_positioning(node, parent_node):
    """Phase 4: layoutPositioningを判定"""
    # 直接プロパティがある場合
    layout_positioning = node.get("layoutPositioning")
    if layout_positioning:
        return layout_positioning
    
    # 判定ロジック
    node_layout_mode = node.get("layoutMode")
    
    if parent_node:
        parent_layout_mode = parent_node.get("layoutMode")
        
        # 親がAuto Layoutなのに自分はNONE = 絶対配置
        if node_layout_mode == "NONE" and parent_layout_mode in ["HORIZONTAL", "VERTICAL"]:
            return "ABSOLUTE"
    
    # Auto Layout内の通常配置
    if node_layout_mode in ["HORIZONTAL", "VERTICAL"]:
        return "AUTO"
    
    # 両方フリーレイアウト = 通常配置
    if node_layout_mode == "NONE":
        if parent_node and parent_node.get("layoutMode") == "NONE":
            return "AUTO"
        elif not parent_node:
            return "AUTO"
    
    return "AUTO"


def format_value_for_markdown(value):
    """値をMarkdown出力用にフォーマット (改行情報を保持)"""
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        return value.replace("|", "\\|").replace("\n", " <br> ")
    if isinstance(value, list):
        if len(value) == 0:
            return None
        json_str = json.dumps(value, ensure_ascii=False)
        if len(json_str) > 100:
            return json_str[:100] + "..."
        return json_str
    if isinstance(value, dict):
        json_str = json.dumps(value, ensure_ascii=False)
        if len(json_str) > 100:
            return json_str[:100] + "..."
        return json_str
    return str(value)


def extract_hyperlink_info(node):
    """テキストノードからリンク情報を抽出"""
    hyperlink = node.get("hyperlink")
    if hyperlink:
        if hyperlink.get("type") == "URL":
            return hyperlink.get("url")
        elif hyperlink.get("type") == "NODE":
            return f"NODE:{hyperlink.get('nodeId')}"
    
    hyperlink_table = node.get("hyperlinkOverrideTable")
    if hyperlink_table:
        links = []
        for key, link_data in hyperlink_table.items():
            if link_data.get("type") == "URL":
                links.append(f"[{key}]:{link_data.get('url')}")
            elif link_data.get("type") == "NODE":
                links.append(f"[{key}]:NODE:{link_data.get('nodeId')}")
        if links:
            return " | ".join(links)
    
    return None


def extract_node_properties_dynamic(node, node_type, whitelist, current_path):
    """ホワイトリストに基づいてノードのプロパティを動的に抽出"""
    dims = get_dimensions(node)

    info = {
        "name": node.get("name", "Unknown"),
        "path": current_path,
        "width": dims.get("width"),
        "height": dims.get("height"),
    }

    whitelist_props = get_type_properties(whitelist, node_type)

    for key in node.keys():
        if key in BLACKLIST_PROPS:
            continue
        if key in ["name", "absoluteBoundingBox", "absoluteRenderBounds"]:
            continue

        value = node.get(key)
        if value is None:
            continue

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

            if key == "fills":
                info["fill"] = converted
            elif key == "strokes":
                info["stroke"] = converted
            else:
                info[key] = converted
        else:
            info[key] = value

    return info


def is_decorative_element(node, dims, parent_info):
    """装飾要素(擬似要素候補)かどうかを判定"""
    height = dims.get("height", 0) or 0
    is_thin = height <= 5
    fills = node.get("fills", [])
    strokes = node.get("strokes", [])
    has_stroke_only = bool(strokes) and not any(f.get("visible", True) for f in fills)
    parent_has_layout = (
        parent_info and
        parent_info.get("itemSpacing") is not None
    )
    return is_thin and has_stroke_only and parent_has_layout


def calculate_pseudo_element_css(parent_gap, element_height):
    """擬似要素用のCSS値を計算"""
    css_gap = parent_gap * 2 + element_height
    css_bottom = -(parent_gap + element_height / 2)
    return css_gap, css_bottom

def build_id_to_node_map(node, id_map=None):
    """全ノードのIDと名前のマッピングを構築"""
    if id_map is None:
        id_map = {}
    
    node_id = node.get("id")
    node_name = node.get("name", "Unknown")
    
    if node_id:
        id_map[node_id] = node_name
    
    children = node.get("children", [])
    for child in children:
        build_id_to_node_map(child, id_map)
    
    return id_map
# ↑↑↑ ここまで追加 ↑↑↑


def traverse_nodes(node, path="", results=None, warnings=None, whitelist=None, unknown_props=None, parent_info=None, depth=0, parent_id=None, parent_node=None, all_elements=None, id_to_name_map=None):
    # ↑↑↑ id_to_name_map=None を追加 ↑↑↑
    """ノードを再帰的に走査して情報を抽出"""
    if results is None:
        results = {
            "texts": [],
            "frames": [],
            "rectangles": [],
            "vectors": [],
            "lines": [],
            "ellipses": [],
            "decoratives": [],
            "parent_gaps": [],
        }
    if warnings is None:
        warnings = []
    if unknown_props is None:
        unknown_props = {}
    if all_elements is None:
        all_elements = []
    if id_to_name_map is None:  # ← 追加
        id_to_name_map = {}      # ← 追加

    node_type = node.get("type", "")
    node_name = node.get("name", "Unknown")
    node_id = node.get("id", f"unknown_{id(node)}")
    visible = node.get("visible", True)
    current_path = f"{path}/{node_name}" if path else node_name

    if not visible:
        return results, warnings, unknown_props, all_elements

    if whitelist:
        detect_unknown_properties(node, node_type, whitelist, unknown_props)

    # Phase 4: 絶対座標を取得
    abs_x, abs_y = get_absolute_position(node)
    
    # Phase 4: layoutPositioningを判定
    layout_positioning = determine_layout_positioning(node, parent_node)
    
    # Phase 5: parent_name を取得
    parent_name = id_to_name_map.get(parent_id, None) if parent_id else None

    # テキスト要素
    if node_type == "TEXT":
        font_family, font_style = get_font_style(node)
        dims = get_dimensions(node)
        style = node.get("style", {})
        font_weight = style.get("fontWeight") or style_to_weight(font_style)

        if not font_family:
            font_family = style.get("fontFamily")

        hyperlink_url = extract_hyperlink_info(node)
        char_style_overrides = node.get("characterStyleOverrides")
        has_mixed_styles = char_style_overrides is not None and len(set(char_style_overrides)) > 1

        line_height_value, line_height_unit = extract_line_height_with_unit(node)

        text_info = {
            "id": node_id,
            "name": node_name,
            "type": node_type,
            "path": current_path,
            "depth": depth,
            "parent_id": parent_id,
            "parent_name": parent_name,  
            "absoluteX": abs_x,
            "absoluteY": abs_y,
            "characters": node.get("characters", ""),
            "fontSize": style.get("fontSize") or node.get("fontSize"),
            "fontWeight": font_weight,
            "fontFamily": font_family,
            "lineHeight": line_height_value,
            "lineHeightUnit": line_height_unit,
            "letterSpacing": style.get("letterSpacing") or node.get("letterSpacing"),
            "textAlign": style.get("textAlignHorizontal") or node.get("textAlignHorizontal"),
            "color": extract_color(node.get("fills", [])),
            "opacity": node.get("opacity", 1),
            "width": dims.get("width"),
            "height": dims.get("height"),
            "hyperlink": hyperlink_url,
            "hasMixedStyles": has_mixed_styles,
            "layoutAlign": node.get("layoutAlign"),
            "layoutGrow": node.get("layoutGrow"),
            "layoutSizingHorizontal": node.get("layoutSizingHorizontal"),
            "layoutSizingVertical": node.get("layoutSizingVertical"),
            "layoutPositioning": layout_positioning,
            "visible": node.get("visible", True),
            "blendMode": node.get("blendMode"),
        }

        if text_info["fontSize"] is None:
            warnings.append(f"⚠️ fontSize未取得: {node_name} (path: {current_path})")

        results["texts"].append(text_info)
        all_elements.append(text_info)

    # フレーム/コンポーネント
    elif node_type in ["FRAME", "COMPONENT", "INSTANCE", "GROUP"]:
        dims = get_dimensions(node)
        item_spacing = node.get("itemSpacing")
        
        component_props = extract_component_properties(node) if node_type == "INSTANCE" else None
        overrides = extract_overrides(node) if node_type == "INSTANCE" else None
        
        corner_radii = node.get("rectangleCornerRadii")
        corner_radii_str = None
        if corner_radii and isinstance(corner_radii, list) and len(corner_radii) == 4:
            corner_radii_str = f"[{corner_radii[0]}, {corner_radii[1]}, {corner_radii[2]}, {corner_radii[3]}]"
        
        overflow_scrolling = node.get("overflowScrolling")
        export_info = extract_export_info(node)
        
        frame_info = {
            "id": node_id,
            "name": node_name,
            "type": node_type,
            "path": current_path,
            "depth": depth,
            "parent_id": parent_id,
            "parent_name": parent_name, 
            "absoluteX": abs_x,
            "absoluteY": abs_y,
            "width": dims.get("width"),
            "height": dims.get("height"),
            "x": dims.get("x"),
            "y": dims.get("y"),
            "paddingTop": node.get("paddingTop"),
            "paddingRight": node.get("paddingRight"),
            "paddingBottom": node.get("paddingBottom"),
            "paddingLeft": node.get("paddingLeft"),
            "itemSpacing": item_spacing,
            "counterAxisSpacing": node.get("counterAxisSpacing"),
            "cornerRadius": node.get("cornerRadius"),
            "rectangleCornerRadii": corner_radii_str,
            "backgroundColor": extract_color(node.get("fills", [])),
            "borderColor": extract_stroke_color(node.get("strokes", [])),
            "strokeWeight": node.get("strokeWeight"),
            "layoutMode": node.get("layoutMode"),
            "layoutWrap": node.get("layoutWrap"),
            "overflowDirection": node.get("overflowDirection"),
            "overflowScrolling": overflow_scrolling,
            "primaryAxisAlignItems": node.get("primaryAxisAlignItems"),
            "counterAxisAlignItems": node.get("counterAxisAlignItems"),
            "counterAxisAlignContent": node.get("counterAxisAlignContent"),
            "layoutSizingHorizontal": node.get("layoutSizingHorizontal"),
            "layoutSizingVertical": node.get("layoutSizingVertical"),
            "primaryAxisSizingMode": node.get("primaryAxisSizingMode"),
            "counterAxisSizingMode": node.get("counterAxisSizingMode"),
            "minWidth": node.get("minWidth"),
            "maxWidth": node.get("maxWidth"),
            "minHeight": node.get("minHeight"),
            "maxHeight": node.get("maxHeight"),
            "layoutAlign": node.get("layoutAlign"),
            "layoutGrow": node.get("layoutGrow"),
            "layoutPositioning": layout_positioning,
            "visible": node.get("visible", True),
            "clipsContent": node.get("clipsContent"),
            "strokeAlign": node.get("strokeAlign"),
            "individualStrokeWeights": node.get("individualStrokeWeights"),
            "constraints": node.get("constraints"),
            "cornerSmoothing": node.get("cornerSmoothing"),
            "blendMode": node.get("blendMode"),
            "opacity": node.get("opacity", 1),
            "effects": extract_effects(node.get("effects", [])),
            "componentProperties": component_props,
            "overrides": overrides,
            "exportSettings": export_info,
        }
        
        results["frames"].append(frame_info)
        all_elements.append(frame_info)

        if item_spacing is not None:
            gap_info = {
                "name": node_name,
                "path": current_path,
                "itemSpacing": item_spacing,
                "layoutMode": node.get("layoutMode"),
            }
            existing_paths = [g["path"] for g in results["parent_gaps"]]
            if current_path not in existing_paths:
                results["parent_gaps"].append(gap_info)

    # 矩形
    elif node_type == "RECTANGLE":
        dims = get_dimensions(node)
        rect_info = extract_node_properties_dynamic(node, node_type, whitelist, current_path)
        rect_info["id"] = node_id
        rect_info["type"] = node_type
        rect_info["depth"] = depth
        rect_info["parent_id"] = parent_id
        rect_info["parent_name"] = parent_name 
        rect_info["absoluteX"] = abs_x
        rect_info["absoluteY"] = abs_y
        rect_info["layoutPositioning"] = layout_positioning
        
        corner_radii = node.get("rectangleCornerRadii")
        if corner_radii and isinstance(corner_radii, list) and len(corner_radii) == 4:
            rect_info["rectangleCornerRadii"] = f"[{corner_radii[0]}, {corner_radii[1]}, {corner_radii[2]}, {corner_radii[3]}]"
        
        export_info = extract_export_info(node)
        if export_info:
            rect_info["exportSettings"] = export_info

        if is_decorative_element(node, dims, parent_info):
            element_height = dims.get("height") or node.get("strokeWeight") or 1
            parent_gap = parent_info.get("itemSpacing", 0)
            css_gap, css_bottom = calculate_pseudo_element_css(parent_gap, element_height)

            decorative_info = {
                "name": node_name,
                "path": current_path,
                "depth": depth,
                "parent_id": parent_id,
                "type": node_type,
                "height": element_height,
                "width": dims.get("width"),
                "color": extract_stroke_color(node.get("strokes", [])) or extract_color(node.get("fills", [])),
                "strokeWeight": node.get("strokeWeight"),
                "parent_name": parent_info.get("name") if parent_info else None,
                "parent_path": parent_info.get("path") if parent_info else None,
                "parent_gap": parent_gap,
                "css_gap": round(css_gap, 2),
                "css_bottom": round(css_bottom, 2),
            }
            results["decoratives"].append(decorative_info)
        else:
            results["rectangles"].append(rect_info)
            all_elements.append(rect_info)

    # ベクター
    elif node_type == "VECTOR":
        dims = get_dimensions(node)
        vector_info = extract_node_properties_dynamic(node, node_type, whitelist, current_path)
        vector_info["id"] = node_id
        vector_info["parent_name"] = parent_name  # ← 追加
        vector_info["type"] = node_type
        vector_info["depth"] = depth
        vector_info["parent_id"] = parent_id
        vector_info["absoluteX"] = abs_x
        vector_info["absoluteY"] = abs_y
        vector_info["layoutPositioning"] = layout_positioning
        
        svg_hash = extract_svg_hash(node)
        if svg_hash:
            vector_info["svgHash"] = svg_hash
        
        export_info = extract_export_info(node)
        if export_info:
            vector_info["exportSettings"] = export_info

        if is_decorative_element(node, dims, parent_info):
            element_height = dims.get("height") or node.get("strokeWeight") or 1
            parent_gap = parent_info.get("itemSpacing", 0)
            css_gap, css_bottom = calculate_pseudo_element_css(parent_gap, element_height)

            decorative_info = {
                "name": node_name,
                "path": current_path,
                "depth": depth,
                "parent_id": parent_id,
                "type": node_type,
                "height": element_height,
                "width": dims.get("width"),
                "color": extract_stroke_color(node.get("strokes", [])) or extract_color(node.get("fills", [])),
                "strokeWeight": node.get("strokeWeight"),
                "parent_name": parent_info.get("name") if parent_info else None,
                "parent_path": parent_info.get("path") if parent_info else None,
                "parent_gap": parent_gap,
                "css_gap": round(css_gap, 2),
                "css_bottom": round(css_bottom, 2),
            }
            results["decoratives"].append(decorative_info)
        else:
            results["vectors"].append(vector_info)
            all_elements.append(vector_info)

    # 線
    elif node_type == "LINE":
        dims = get_dimensions(node)
        line_info = extract_node_properties_dynamic(node, node_type, whitelist, current_path)
        line_info["id"] = node_id
        line_info["parent_name"] = parent_name  # ← 追加
        line_info["type"] = node_type
        line_info["depth"] = depth
        line_info["parent_id"] = parent_id
        line_info["absoluteX"] = abs_x
        line_info["absoluteY"] = abs_y
        line_info["layoutPositioning"] = layout_positioning

        if is_decorative_element(node, dims, parent_info):
            element_height = dims.get("height") or node.get("strokeWeight") or 1
            parent_gap = parent_info.get("itemSpacing", 0)
            css_gap, css_bottom = calculate_pseudo_element_css(parent_gap, element_height)

            decorative_info = {
                "name": node_name,
                "path": current_path,
                "depth": depth,
                "parent_id": parent_id,
                "type": node_type,
                "height": element_height,
                "width": dims.get("width"),
                "color": extract_stroke_color(node.get("strokes", [])) or extract_color(node.get("fills", [])),
                "strokeWeight": node.get("strokeWeight"),
                "parent_name": parent_info.get("name") if parent_info else None,
                "parent_path": parent_info.get("path") if parent_info else None,
                "parent_gap": parent_gap,
                "css_gap": round(css_gap, 2),
                "css_bottom": round(css_bottom, 2),
            }
            results["decoratives"].append(decorative_info)
        else:
            results["lines"].append(line_info)
            all_elements.append(line_info)

    # 楕円
    elif node_type == "ELLIPSE":
        ellipse_info = extract_node_properties_dynamic(node, node_type, whitelist, current_path)
        ellipse_info["id"] = node_id
        ellipse_info["parent_name"] = parent_name  # ← 追加
        ellipse_info["type"] = node_type
        ellipse_info["depth"] = depth
        ellipse_info["parent_id"] = parent_id
        ellipse_info["absoluteX"] = abs_x
        ellipse_info["absoluteY"] = abs_y
        ellipse_info["layoutPositioning"] = layout_positioning
        
        export_info = extract_export_info(node)
        if export_info:
            ellipse_info["exportSettings"] = export_info
        
        results["ellipses"].append(ellipse_info)
        all_elements.append(ellipse_info)

    # その他のノードタイプ
    elif node_type in ["BOOLEAN_OPERATION", "STAR", "REGULAR_POLYGON"]:
        other_info = extract_node_properties_dynamic(node, node_type, whitelist, current_path)
        other_info["id"] = node_id
        other_info["parent_name"] = parent_name  # ← 追加
        other_info["type"] = node_type
        other_info["depth"] = depth
        other_info["parent_id"] = parent_id
        other_info["absoluteX"] = abs_x
        other_info["absoluteY"] = abs_y
        other_info["layoutPositioning"] = layout_positioning
        
        svg_hash = extract_svg_hash(node)
        if svg_hash:
            other_info["svgHash"] = svg_hash
        
        export_info = extract_export_info(node)
        if export_info:
            other_info["exportSettings"] = export_info
        
        results["vectors"].append(other_info)
        all_elements.append(other_info)

    # 親情報を作成
    current_parent_info = None
    if node_type in ["FRAME", "COMPONENT", "INSTANCE", "GROUP"]:
        item_spacing = node.get("itemSpacing")
        if item_spacing is not None:
            current_parent_info = {
                "name": node_name,
                "path": current_path,
                "itemSpacing": item_spacing,
                "layoutMode": node.get("layoutMode"),
            }

    # 子要素を再帰処理
    children = node.get("children", [])
    for child in children:
        child_parent_info = current_parent_info if current_parent_info else parent_info
        traverse_nodes(
            child, 
            current_path, 
            results, 
            warnings, 
            whitelist, 
            unknown_props, 
            child_parent_info,
            depth + 1,
            node_id,
            node,
            all_elements,
            id_to_name_map 
        )

    return results, warnings, unknown_props, all_elements


# Phase 4: 重なり検出ロジック
def is_parent_child_relationship(elem_a, elem_b):
    """親子関係かどうかを判定"""
    if abs(elem_a.get('depth', 0) - elem_b.get('depth', 0)) == 1:
        if elem_a.get('parent_id') == elem_b.get('id') or \
           elem_b.get('parent_id') == elem_a.get('id'):
            return True
    return False


def is_decorative_for_overlap(elem):
    """装飾要素かどうかを判定（重なり検出用）"""
    decorative_patterns = [
        'star',
        'decoration',
        'ornament',
        'bg',
        'background'
    ]
    
    # LINEタイプは装飾要素
    if elem.get('type') == 'LINE':
        return True
    
    # 名前による判定
    name_lower = elem.get('name', '').lower()
    if any(pattern in name_lower for pattern in decorative_patterns):
        return True
    
    # VectorやEllipseで特定のパターン
    if elem.get('type') in ['VECTOR', 'ELLIPSE']:
        # 小さなアイコン
        width = elem.get('width', 0) or 0
        height = elem.get('height', 0) or 0
        if width < 150 and height < 150:
            return True
    
    return False


def should_exclude_from_overlap(elem_a, elem_b):
    """重なり検出から除外すべきかを判定"""
    # 親子関係
    if is_parent_child_relationship(elem_a, elem_b):
        return True
    
    # Line要素
    if elem_a.get('type') == 'LINE' or elem_b.get('type') == 'LINE':
        return True
    
    # 必須データがない
    for elem in [elem_a, elem_b]:
        if not all(k in elem and elem[k] is not None for k in ['absoluteX', 'absoluteY', 'width', 'height']):
            return True
    
    # 完全包含（elem_aがelem_bに完全に含まれる）
    a_left = elem_a.get('absoluteX', 0)
    a_top = elem_a.get('absoluteY', 0)
    a_right = a_left + (elem_a.get('width', 0) or 0)
    a_bottom = a_top + (elem_a.get('height', 0) or 0)
    
    b_left = elem_b.get('absoluteX', 0)
    b_top = elem_b.get('absoluteY', 0)
    b_right = b_left + (elem_b.get('width', 0) or 0)
    b_bottom = b_top + (elem_b.get('height', 0) or 0)
    
    if (a_left >= b_left and a_top >= b_top and a_right <= b_right and a_bottom <= b_bottom):
        return True
    
    # 極小要素（アイコン等）
    if (elem_a.get('width', 0) or 0) < 30 and (elem_a.get('height', 0) or 0) < 30:
        return True
    
    return False


def calculate_x_overlap(a_left, a_right, b_left, b_right):
    """X軸の重なり幅を計算"""
    overlap_start = max(a_left, b_left)
    overlap_end = min(a_right, b_right)
    return max(0, overlap_end - overlap_start)


def to_css_class(name):
    """Figma要素名をCSSクラス名に変換"""
    import re
    # 括弧を削除し、スペースをハイフンに
    name = re.sub(r'[()]', '', name)
    name = name.lower().replace(' ', '-')
    # 連続するハイフンを1つに
    name = re.sub(r'-+', '-', name)
    return name.strip('-')


def generate_css_suggestion(elem_a, elem_b, overlap_y, overlap_x):
    """推奨CSS実装方法を生成"""
    class_a = to_css_class(elem_a.get('name', ''))
    class_b = to_css_class(elem_b.get('name', ''))
    
    # 絶対配置の場合
    if elem_a.get('layoutPositioning') == 'ABSOLUTE':
        abs_x = elem_a.get('absoluteX', 0) or 0
        abs_y = elem_a.get('absoluteY', 0) or 0
        return f"`.{class_a} {{ position: absolute; top: {abs_y}px; left: {abs_x}px; z-index: 10; }}`"
    
    # 負のマージンを使う場合
    overlap_y_int = int(round(overlap_y))
    return f"`.{class_a} {{ position: relative; margin-bottom: -{overlap_y_int}px; z-index: 10; }}` + `.{class_b} {{ padding-top: {overlap_y_int}px; }}`"


def generate_decorative_css(elem_a, elem_b):
    """装飾要素用のCSS実装方法を生成"""
    parent_class = to_css_class(elem_b.get('name', ''))
    abs_x = elem_a.get('absoluteX', 0) or 0
    abs_y = elem_a.get('absoluteY', 0) or 0
    width = elem_a.get('width', 0) or 0
    height = elem_a.get('height', 0) or 0
    
    # 親要素の座標からの相対位置を計算
    parent_x = elem_b.get('absoluteX', 0) or 0
    parent_y = elem_b.get('absoluteY', 0) or 0
    rel_x = abs_x - parent_x
    rel_y = abs_y - parent_y
    
    color = elem_a.get('fill') or elem_a.get('stroke') or 'rgb(0,0,0)'
    
    return f"`.{parent_class}::before {{ content: ''; position: absolute; top: {rel_y}px; left: {rel_x}px; width: {width}px; height: {height}px; background: {color}; }}`"


def detect_overlaps(all_elements):
    """全要素から重なりを検出する"""
    overlaps = []
    decorative_overlaps = []
    
    # Y座標でソート（上から順）
    sorted_elements = sorted(
        [e for e in all_elements if e.get('absoluteY') is not None],
        key=lambda e: e.get('absoluteY', 0)
    )
    
    for i, elem_a in enumerate(sorted_elements):
        # 必須プロパティの確認
        if not all(k in elem_a and elem_a[k] is not None for k in ['absoluteX', 'absoluteY', 'width', 'height']):
            continue
        
        a_bottom = elem_a['absoluteY'] + elem_a['height']
        
        for elem_b in sorted_elements[i+1:]:
            if not all(k in elem_b and elem_b[k] is not None for k in ['absoluteX', 'absoluteY', 'width', 'height']):
                continue
            
            b_top = elem_b['absoluteY']
            
            # Y座標の差が大きすぎる場合はスキップ
            if b_top - a_bottom > 500:
                break
            
            # 除外判定
            if should_exclude_from_overlap(elem_a, elem_b):
                continue
            
            # Y軸の重なりチェック
            if a_bottom > b_top:
                overlap_y = a_bottom - b_top
                
                # X軸の重なりチェック
                a_left = elem_a['absoluteX']
                a_right = a_left + elem_a['width']
                b_left = elem_b['absoluteX']
                b_right = b_left + elem_b['width']
                
                # X軸で重なっているか
                if not (a_right <= b_left or b_right <= a_left):
                    overlap_x = calculate_x_overlap(a_left, a_right, b_left, b_right)
                    
                    overlap_info = {
                        'element_a_name': elem_a.get('name', 'Unknown'),
                        'element_a_id': elem_a.get('id', '-'),
                        'element_b_name': elem_b.get('name', 'Unknown'),
                        'element_b_id': elem_b.get('id', '-'),
                        'overlap_y': round(overlap_y, 1),
                        'overlap_x': round(overlap_x, 1),
                    }
                    
                    # 装飾要素判定
                    if is_decorative_for_overlap(elem_a):
                        overlap_info['css_suggestion'] = generate_decorative_css(elem_a, elem_b)
                        decorative_overlaps.append(overlap_info)
                    else:
                        overlap_info['css_suggestion'] = generate_css_suggestion(elem_a, elem_b, overlap_y, overlap_x)
                        overlaps.append(overlap_info)
    
    return overlaps, decorative_overlaps


def generate_dynamic_table(title, items):
    """アイテムのリストから動的にMarkdownテーブルを生成"""
    if not items:
        return []

    lines = []
    lines.append(f"## {title}")
    lines.append("")

    all_keys = []
    seen_keys = set()

    # Phase 4: AbsoluteX/Yを優先キーに追加
    priority_keys = ["Characters", "name", "depth", "parent_id", "absoluteX", "absoluteY", "width", "height", 
                     "fill", "stroke", "strokeWeight",
                     "cornerRadius", "rectangleCornerRadii", "svgHash", "exportSettings", 
                     "strokeCap", "strokeJoin", "opacity", "layoutPositioning"]

    for key in priority_keys:
        for item in items:
            if key in item and key not in seen_keys:
                all_keys.append(key)
                seen_keys.add(key)
                break

    for item in items:
        for key in item.keys():
            if key not in seen_keys and key not in SKIP_IN_OUTPUT and key not in ['id', 'type']:
                all_keys.append(key)
                seen_keys.add(key)

    header = "| " + " | ".join(all_keys) + " |"
    separator = "|" + "|".join(["------" for _ in all_keys]) + "|"
    lines.append(header)
    lines.append(separator)

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


def generate_markdown(results, warnings, input_file, unknown_props=None, added_props=None, all_elements=None):
    """抽出結果をMarkdown形式で出力"""
    lines = []

    lines.append(f"# Figma Design Data (Optimized for AI Coding)")
    lines.append(f"")
    lines.append(f"Source: `{input_file}`")
    lines.append(f"")
    lines.append(f"> 注意：セクション名はFigmaの構造に基づきます。内容から適切なHTMLタグを推論してください。")
    lines.append(f"")
    lines.append(f"**実装済み機能:**")
    lines.append(f"- ✅ componentProperties(バリアント情報)")
    lines.append(f"- ✅ rectangleCornerRadii(個別角丸)")
    lines.append(f"- ✅ lineHeight単位情報(PIXELS/PERCENT)")
    lines.append(f"- ✅ 親子関係(depth, parent_id)")
    lines.append(f"- ✅ overflowScrolling(スクロール設定)")
    lines.append(f"- ✅ SVGハッシュ値(アイコン識別)")
    lines.append(f"- ✅ exportSettings(画像情報)")
    lines.append(f"- ✅ **絶対座標(AbsoluteX/Y) - Phase 4**")
    lines.append(f"- ✅ **layoutPositioning判定 - Phase 4**")
    lines.append(f"- ✅ **要素の重なり検出と推奨CSS提案 - Phase 4**")
    lines.append(f"")

    if warnings or unknown_props or added_props:
        lines.append("## ⚠️ Warnings")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        if added_props:
            lines.append(f"- 🆕 ホワイトリストに追加されたプロパティ: {', '.join(added_props)}")
        lines.append("")

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
    lines.append(f"| **Decoratives (擬似要素候補)** | **{len(results['decoratives'])}** |")
    lines.append("")

    # テキスト要素 (基本)
    if results["texts"]:
        lines.append("## Texts (基本)")
        lines.append("")
        lines.append("| Characters | Name | fontSize | fontWeight | AbsoluteX | AbsoluteY | color | lineHeight | textAlign | opacity |")
        lines.append("|------------|------|----------|------------|-----------|-----------|-------|------------|-----------|---------|")
        for t in results["texts"]:
            chars = t["characters"][:50] + "..." if len(t["characters"]) > 50 else t["characters"]
            chars = chars.replace("|", "\\|")
            text_align = t.get('textAlign', '-')
            abs_x = t.get('absoluteX', '-') or '-'
            abs_y = t.get('absoluteY', '-') or '-'
            line_height = t.get('lineHeight', '-')
            parent_name = t.get('parent_name', '-') or '-'
            # 数値の丸め処理
            font_size = round(t['fontSize']) if t['fontSize'] else "-"
            font_weight = t['fontWeight'] if t['fontWeight'] else "-"
            abs_x_rounded = round(abs_x) if abs_x != '-' and abs_x is not None else "-"
            abs_y_rounded = round(abs_y) if abs_y != '-' and abs_y is not None else "-"
            line_height_rounded = round(line_height) if line_height != '-' and line_height is not None else "-"
            opacity = round(t.get('opacity', 1), 1) if t.get('opacity', 1) != 1 else "-"

            lines.append(f"| {chars} | {t['name']} | {font_size} | {font_weight} | {abs_x_rounded} | {abs_y_rounded} | {t['color']} | {line_height_rounded} | {text_align} | {opacity} |")
        lines.append("")

        # テキスト要素 (レイアウト詳細)
        lines.append("## Texts (レイアウト詳細)")
        lines.append("")
        lines.append("| Name | Parent ID | LayoutPositioning | Sizing H | Sizing V | Grow | Align | Visible | BlendMode | Opacity |")
        lines.append("|------|-----------|-------------------|----------|----------|------|-------|---------|-----------|---------|")
        for t in results["texts"]:
            parent_id = t.get('parent_id', '-') or "-"
            layout_pos = t.get('layoutPositioning', '-') or "-"
            sizing_h = t.get('layoutSizingHorizontal', '-') or "-"
            sizing_v = t.get('layoutSizingVertical', '-') or "-"
            grow = t.get('layoutGrow')
            grow_str = str(grow) if grow is not None else "-"
            align = t.get('layoutAlign', '-') or "-"
            visible = t.get('visible', True)
            visible_str = "-" if visible is True else "✗ hidden"
            blend = t.get('blendMode', '-') or "-"
            blend_str = "-" if blend == "PASS_THROUGH" else blend
            opacity = t.get('opacity', 1)
            opacity_str = str(opacity) if opacity != 1 else "-"
            lines.append(f"| {t['name'][:20]} | {parent_id[:15]} | {layout_pos} | {sizing_h} | {sizing_v} | {grow_str} | {align} | {visible_str} | {blend_str} | {opacity_str} |")
        lines.append("")

    # フレーム/コンポーネント(基本情報)
    if results["frames"]:
        lines.append("## Frames & Components (基本)")
        lines.append("")
        lines.append("| Name | Type | Width | Height | AbsoluteX | AbsoluteY | layoutMode | itemSpacing | backgroundColor | cornerRadius |")
        lines.append("|------|------|-------|--------|-----------|-----------|------------|-------------|-----------------|-------------|")
        for f in results["frames"]:
            abs_x = f.get('absoluteX', '-') or '-'
            abs_y = f.get('absoluteY', '-') or '-'
            # 数値の丸め処理
            width_rounded = round(f['width']) if f['width'] else "-"
            height_rounded = round(f['height']) if f['height'] else "-"
            abs_x_rounded = round(abs_x) if abs_x != '-' and abs_x is not None else "-"
            abs_y_rounded = round(abs_y) if abs_y != '-' and abs_y is not None else "-"
            item_spacing_rounded = round(f['itemSpacing']) if f['itemSpacing'] else "-"
            corner_radius_rounded = round(f['cornerRadius']) if f['cornerRadius'] else "-"

            lines.append(f"| {f['name']} | {f['type']} | {width_rounded} | {height_rounded} | {abs_x_rounded} | {abs_y_rounded} | {f['layoutMode']} | {item_spacing_rounded} | {f['backgroundColor']} | {corner_radius_rounded} |")
        lines.append("")

        # フレーム/コンポーネント(レイアウト詳細)
        lines.append("## Frames & Components (レイアウト詳細)")
        lines.append("")
        lines.append("| Name | Parent ID | Layout | LayoutPositioning | Wrap | OverflowScroll | Align (Primary) | Align (Counter) | Sizing H | Sizing V | Grow | ChildAlign |")
        lines.append("|------|-----------|--------|-------------------|------|----------------|-----------------|-----------------|----------|----------|------|------------|")
        for f in results["frames"]:
            parent_id = f.get('parent_id', '-') or "-"
            layout = f.get('layoutMode', '-') or "-"
            layout_pos = f.get('layoutPositioning', '-') or "-"
            layout_wrap = f.get('layoutWrap', '-') or "-"
            overflow_scroll = f.get('overflowScrolling', '-') or "-"
            primary_align = f.get('primaryAxisAlignItems', '-') or "-"
            counter_align = f.get('counterAxisAlignItems', '-') or "-"
            sizing_h = f.get('layoutSizingHorizontal', '-') or "-"
            sizing_v = f.get('layoutSizingVertical', '-') or "-"
            grow = f.get('layoutGrow')
            grow_str = str(grow) if grow is not None else "-"
            child_align = f.get('layoutAlign', '-') or "-"
            lines.append(f"| {f['name']} | {parent_id[:15]} | {layout} | {layout_pos} | {layout_wrap} | {overflow_scroll} | {primary_align} | {counter_align} | {sizing_h} | {sizing_v} | {grow_str} | {child_align} |")
        lines.append("")

        # フレーム/コンポーネント(表示・その他)
        lines.append("## Frames & Components (表示・その他)")
        lines.append("")
        lines.append("| Name | Visible | ClipsContent | StrokeAlign | BlendMode | Opacity | Constraints | Overrides |")
        lines.append("|------|---------|--------------|-------------|-----------|---------|-------------|-----------|")
        for f in results["frames"]:
            visible = f.get('visible', True)
            visible_str = "-" if visible is True else "✗ hidden"
            clips = f.get('clipsContent')
            clips_str = "✓ clip" if clips is True else "-"
            stroke_align = f.get('strokeAlign', '-') or "-"
            blend = f.get('blendMode', '-') or "-"
            blend_str = "-" if blend == "PASS_THROUGH" else blend
            opacity = f.get('opacity', 1)
            opacity_str = str(opacity) if opacity != 1 else "-"
            constraints = f.get('constraints')
            if constraints:
                constraints_str = f"V:{constraints.get('vertical', '-')}/H:{constraints.get('horizontal', '-')}"
            else:
                constraints_str = "-"
            overrides = f.get('overrides', '-') or "-"
            lines.append(f"| {f['name']} | {visible_str} | {clips_str} | {stroke_align} | {blend_str} | {opacity_str} | {constraints_str} | {overrides} |")
        lines.append("")

    # 矩形(動的カラム生成)
    if results["rectangles"]:
        lines.extend(generate_dynamic_table("Rectangles", results["rectangles"]))

    # ベクター(動的カラム生成)
    if results["vectors"]:
        lines.extend(generate_dynamic_table("Vectors (Icons/Lines)", results["vectors"]))

    # 線(動的カラム生成)
    if results["lines"]:
        lines.extend(generate_dynamic_table("Lines", results["lines"]))

    # 楕円(動的カラム生成)
    if results["ellipses"]:
        lines.extend(generate_dynamic_table("Ellipses", results["ellipses"]))

    # Phase 4: 重なり検出セクション
    if all_elements:
        overlaps, decorative_overlaps = detect_overlaps(all_elements)
        
        if overlaps or decorative_overlaps:
            lines.append("## 🔴 Layout Overlaps (要素の重なり検出)")
            lines.append("")
            lines.append("以下の要素は画面上で重なっています。コーディング時に`position`、`margin`、`z-index`の調整が必要です。")
            lines.append("")
            
            if overlaps:
                lines.append("### 通常要素の重なり")
                lines.append("")
                lines.append("| Element A (前面) | Element A ID | Element B (背面) | Element B ID | Y軸重なり (px) | X軸重なり (px) | 推奨CSS実装方法 |")
                lines.append("|-----------------|-------------|-----------------|-------------|---------------|---------------|----------------|")
                for overlap in overlaps:
                    lines.append(f"| {overlap['element_a_name']} | {overlap['element_a_id']} | {overlap['element_b_name']} | {overlap['element_b_id']} | {overlap['overlap_y']} | {overlap['overlap_x']} | {overlap['css_suggestion']} |")
                lines.append("")
            
            if decorative_overlaps:
                lines.append("### 装飾要素の重なり")
                lines.append("")
                lines.append("| Element A (装飾) | Element A ID | Element B (背景) | Element B ID | 配置方法 |")
                lines.append("|-----------------|-------------|-----------------|-------------|---------|")
                for overlap in decorative_overlaps:
                    lines.append(f"| {overlap['element_a_name']} | {overlap['element_a_id']} | {overlap['element_b_name']} | {overlap['element_b_id']} | {overlap['css_suggestion']} |")
                lines.append("")
            
            lines.append("**検出条件**:")
            lines.append("- Y軸で重なりがある(Element A の bottom > Element B の top)")
            lines.append("- X軸でも重なりがある(完全に横並びではない)")
            lines.append("- 親子関係ではない(depth差が1かつparent_idが一致する場合は除外)")
            lines.append("")
            lines.append("**注意事項**:")
            lines.append("- `margin-bottom`を負の値にする場合、下の要素に対応する`padding-top`を追加して高さを確保")
            lines.append("- 絶対配置(`position: absolute`)を使う場合、親要素に`position: relative`が必要")
            lines.append("- 装飾要素は`::before`、`::after`擬似要素での実装を推奨")
            lines.append("")

    # 装飾要素 (擬似要素候補)
    if results["decoratives"]:
        lines.append("## 🎨 Decorative Elements (擬似要素候補)")
        lines.append("")
        lines.append("以下の要素は装飾線として検出されました。CSS擬似要素 (`::after`)で実装してください。")
        lines.append("")
        lines.append("| 要素名 | Depth | 親要素 | 元gap | 高さ | 色 | → CSS gap | → bottom |")
        lines.append("|--------|-------|--------|-------|------|-----|-----------|----------|")
        for d in results["decoratives"]:
            name = d.get("name", "-")
            depth = d.get("depth", "-")
            parent = d.get("parent_name", "-")
            parent_gap = d.get("parent_gap", "-")
            height = d.get("height", "-")
            color = d.get("color", "-")
            css_gap = d.get("css_gap", "-")
            css_bottom = d.get("css_bottom", "-")
            parent_gap_str = f"{parent_gap}px" if parent_gap != "-" else "-"
            height_str = f"{height}px" if height != "-" else "-"
            css_gap_str = f"{css_gap}px" if css_gap != "-" else "-"
            css_bottom_str = f"{css_bottom}px" if css_bottom != "-" else "-"
            lines.append(f"| {name} | {depth} | {parent} | {parent_gap_str} | {height_str} | {color} | {css_gap_str} | {css_bottom_str} |")
        lines.append("")
        lines.append("### 実装例")
        lines.append("")
        lines.append("```scss")
        first_dec = results["decoratives"][0]
        parent_name = first_dec.get("parent_name", "parent")
        css_gap = first_dec.get("css_gap", 25)
        css_bottom = first_dec.get("css_bottom", -12.5)
        height = first_dec.get("height", 1)
        color = first_dec.get("color", "rgb(212, 214, 221)")
        lines.append(f".{parent_name.lower().replace(' ', '-')} {{")
        lines.append(f"  display: flex;")
        lines.append(f"  flex-direction: column;")
        lines.append(f"  gap: {css_gap}px;  // 計算済み")
        lines.append(f"}}")
        lines.append(f"")
        lines.append(f".item {{")
        lines.append(f"  position: relative;")
        lines.append(f"  ")
        lines.append(f"  &:not(:last-child)::after {{")
        lines.append(f"    content: '';")
        lines.append(f"    position: absolute;")
        lines.append(f"    bottom: {css_bottom}px;  // 計算済み")
        lines.append(f"    left: 0;")
        lines.append(f"    right: 0;")
        lines.append(f"    height: {height}px;")
        lines.append(f"    background: {color};")
        lines.append(f"  }}")
        lines.append(f"}}")
        lines.append("```")
        lines.append("")

    # AI計算ヘルパー
    if results["parent_gaps"]:
        lines.append("## 📐 AI計算ヘルパー")
        lines.append("")
        lines.append("AIが追加で装飾要素を検出した場合、以下の情報を使って計算してください。")
        lines.append("")
        lines.append("### 親要素のitemSpacing一覧")
        lines.append("")
        lines.append("| 親要素名 | パス | itemSpacing | layoutMode |")
        lines.append("|----------|------|-------------|------------|")
        for g in results["parent_gaps"]:
            name = g.get("name", "-")
            path = g.get("path", "-")
            spacing = g.get("itemSpacing", "-")
            layout = g.get("layoutMode", "-")
            spacing_str = f"{spacing}px" if spacing != "-" else "-"
            lines.append(f"| {name} | {path} | {spacing_str} | {layout} |")
        lines.append("")
        lines.append("### 計算式")
        lines.append("")
        lines.append("```")
        lines.append("CSS gap = 元のgap × 2 + 装飾要素の高さ")
        lines.append("bottom位置 = -(元のgap + 装飾要素の高さ / 2)")
        lines.append("```")
        lines.append("")

    # Phase 3: SVGハッシュ値についての説明を追加
    has_svg_hash = any(v.get("svgHash") for v in results["vectors"])
    if has_svg_hash:
        lines.append("## 🎨 SVGハッシュ値について")
        lines.append("")
        lines.append("**svgHash列の見方:**")
        lines.append("- 同じハッシュ値 = 同じアイコン形状")
        lines.append("- 違うハッシュ値 = 異なるアイコン形状")
        lines.append("- この情報を使って、AIは同じアイコンを統一して使用できます")
        lines.append("")
        lines.append("**例:**")
        lines.append("```")
        lines.append("arrow-icon-01 | svgHash: a3f2b8c1  ← 同じハッシュ")
        lines.append("arrow-icon-02 | svgHash: a3f2b8c1  ← 同じアイコンとして扱える")
        lines.append("trash-icon    | svgHash: 7d9e4f2a  ← 別のアイコン")
        lines.append("```")
        lines.append("")
        # Phase 5: 階層構造（Tree）を出力
        lines.append("## 📐 階層構造（Layout Tree）")
        lines.append("")
        lines.append("この階層構造を参照して、HTMLの入れ子関係を正確に再現してください。")
        lines.append("")
        
        def build_tree_lines(elements, parent_id=None, indent=0):
            """階層構造を再帰的に構築"""
            tree_lines = []
            # parent_idが一致する要素を抽出
            children = [e for e in elements if e.get('parent_id') == parent_id]
            # depthでソート
            children.sort(key=lambda x: (x.get('depth', 0), x.get('absoluteY', 0) or 0))
            
            for elem in children:
                indent_str = "  " * indent
                elem_type = elem.get('type', 'Unknown')
                elem_name = elem.get('name', 'Unknown')
                elem_id = elem.get('id', '')
                
                if elem_type == "TEXT":
                    chars = elem.get('characters', '')[:30]
                    if len(elem.get('characters', '')) > 30:
                        chars += "..."
                    tree_lines.append(f"{indent_str}- {elem_name} (Text): \"{chars}\"")
                else:
                    tree_lines.append(f"{indent_str}- {elem_name} ({elem_type})")
                
                # 子要素を再帰的に追加
                tree_lines.extend(build_tree_lines(elements, elem_id, indent + 1))
            
            return tree_lines
        
        tree_output = build_tree_lines(all_elements)
        lines.extend(tree_output)
        lines.append("")

    return "\n".join(lines)


def main(return_results=False, input_file_override=None):
    # input_file_override が指定されている場合はそれを使用
    if input_file_override:
        input_file = input_file_override
        output_file = None
    else:
        if len(sys.argv) < 2 and not return_results:
            print("Usage: python extract_figma_06.py <figma-data.json> [output.md]")
            sys.exit(1)

        input_file = sys.argv[1] if len(sys.argv) >= 2 else None
        output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if output_file is None and not return_results:
        input_path = Path(input_file)
        output_file = input_path.parent / "extracted.md"

    print(f"Loading whitelist: {WHITELIST_FILE}")
    whitelist = load_whitelist()

    print(f"Reading: {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    root = data
    if "document" in data:
        root = data["document"]
    elif "nodes" in data:
        for node_id, node_data in data["nodes"].items():
            if "document" in node_data:
                root = node_data["document"]
                break
    elif "children" in data:
        pass

    print("Building ID to name map...")
    id_to_name_map = build_id_to_node_map(root)  # ← 追加
    
    print("Extracting (Phase 1-5)...")
    results, warnings, unknown_props, all_elements = traverse_nodes(root, whitelist=whitelist, id_to_name_map=id_to_name_map)  # ← 引数追加

    added_props = []
    if unknown_props:
        print(f"\n🆕 未知のプロパティを検出:")
        for node_type, props in unknown_props.items():
            for prop in props:
                print(f"   {node_type}.{prop}")

        added_props = add_unknown_to_whitelist(whitelist, unknown_props)
        if added_props:
            save_whitelist(whitelist)
            print(f"\n✅ ホワイトリストに追加しました: {', '.join(added_props)}")

    # return_results=True の場合はファイル出力をスキップ
    if not return_results:
        markdown = generate_markdown(results, warnings, input_file, unknown_props, added_props, all_elements)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"\n✅ Output: {output_file}")
    print(f"   Texts: {len(results['texts'])}")
    print(f"   Frames: {len(results['frames'])}")
    print(f"   Rectangles: {len(results['rectangles'])}")
    print(f"   Vectors: {len(results['vectors'])}")
    print(f"   Lines: {len(results['lines'])}")
    print(f"   Ellipses: {len(results['ellipses'])}")
    if results['decoratives']:
        print(f"   🎨 Decoratives (擬似要素候補): {len(results['decoratives'])}")
    
    # Phase 4: 重なり検出結果を表示
    if all_elements:
        overlaps, decorative_overlaps = detect_overlaps(all_elements)
        if overlaps or decorative_overlaps:
            print(f"   🔴 Layout Overlaps: {len(overlaps)} normal, {len(decorative_overlaps)} decorative")

    if warnings:
        print(f"\n⚠️ Warnings: {len(warnings)}")
        for w in warnings:
            print(f"   {w}")
    else:
        print(f"\n✅ No warnings")
    
    print(f"\n📋 Phase 1-4 実装完了:")
    print(f"   ✅ Phase 1: componentProperties, rectangleCornerRadii, lineHeight単位, 親子関係")
    print(f"   ✅ Phase 2: overflowScrolling")
    print(f"   ✅ Phase 3: SVGハッシュ値, exportSettings")
    print(f"   ✅ Phase 4: 絶対座標(AbsoluteX/Y), layoutPositioning, 重なり検出")

    # return_results=True の場合は結果を返す
    if return_results:
        # 重なり検出結果を results に追加
        if all_elements:
            overlaps, decorative_overlaps = detect_overlaps(all_elements)
            results['overlaps'] = overlaps
            results['decorative_overlaps'] = decorative_overlaps
        else:
            results['overlaps'] = []
            results['decorative_overlaps'] = []

        return results, warnings, unknown_props, all_elements


if __name__ == "__main__":
    main()