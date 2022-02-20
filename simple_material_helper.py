bl_info = {
    "name": "Simple Material Helper",
    "description": "Helpers for making using materials simpler.",
    "author": "Dragorn421",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "Panel in material properties",
    "doc_url": "",
    "support": "COMMUNITY",
    "category": "Material",
}

# Copyright (C) 2022 Dragorn421
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import bpy

from pathlib import Path
import json
import traceback

import typing

if typing.TYPE_CHECKING:
    from typing import (
        Optional,
    )


class MaterialNodes:
    image: bpy.types.ShaderNodeTexImage
    uv_repeat_type_u: bpy.types.ShaderNodeValue
    uv_repeat_type_v: bpy.types.ShaderNodeValue


def ensure_setup_and_get_nodes(material: bpy.types.Material):
    node_tree = material.node_tree

    # ensure vertex colors data exists

    for mesh in bpy.data.meshes:
        mesh: bpy.types.Mesh
        if material in mesh.materials.values():
            if mesh.vertex_colors.active is None:
                mesh.vertex_colors.new(do_init=False)

    for object in bpy.data.objects:
        object: bpy.types.Object
        if object.type == "MESH" and material in (
            material_slot.material for material_slot in object.material_slots.values()
        ):
            if object.data.vertex_colors.active is None:
                object.data.vertex_colors.new(do_init=False)

    # output node

    output_node_name = "SMH Output Material"
    output_node = node_tree.nodes.get(output_node_name)
    if output_node is None:
        output_node = node_tree.nodes.new("ShaderNodeOutputMaterial")
        output_node.name = output_node_name
        output_node.location = -200, 0

    other_output_nodes = [
        node
        for node in node_tree.nodes
        if node.bl_idname == "ShaderNodeOutputMaterial" and node != output_node
    ]
    for other_output_node in other_output_nodes:
        node_tree.nodes.remove(other_output_node)

    # shader node

    shader_node_name = "SMH Principled BSDF"
    shader_node = node_tree.nodes.get(shader_node_name)
    if shader_node is None:
        shader_node = node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        shader_node.name = shader_node_name
        shader_node.location = -500, 0

    shader_node.inputs["Specular"].default_value = 0

    # image node

    image_node_name = "SMH Image Texture"
    image_node = node_tree.nodes.get(image_node_name)
    if image_node is None:
        image_node = node_tree.nodes.new("ShaderNodeTexImage")
        image_node.name = image_node_name
        image_node.location = -1300, 0

    # vertex color node

    vertex_color_node_name = "SMH Vertex Color"
    vertex_color_node = node_tree.nodes.get(vertex_color_node_name)
    if vertex_color_node is None:
        vertex_color_node = node_tree.nodes.new("ShaderNodeVertexColor")
        vertex_color_node.name = vertex_color_node_name
        vertex_color_node.location = -1300, -500

    # multiply image color and vertex color node

    multiply_image_color_and_vertex_color_node_name = "SMH Image Color * Vertex Color"
    multiply_image_color_and_vertex_color_node = node_tree.nodes.get(
        multiply_image_color_and_vertex_color_node_name
    )
    if multiply_image_color_and_vertex_color_node is None:
        multiply_image_color_and_vertex_color_node = node_tree.nodes.new(
            "ShaderNodeVectorMath"
        )
        multiply_image_color_and_vertex_color_node.name = (
            multiply_image_color_and_vertex_color_node_name
        )
        multiply_image_color_and_vertex_color_node.location = -800, 0
    multiply_image_color_and_vertex_color_node: bpy.types.ShaderNodeVectorMath
    multiply_image_color_and_vertex_color_node.operation = "MULTIPLY"

    # multiply image alpha and vertex alpha node

    multiply_image_alpha_and_vertex_alpha_node_name = "SMH Image Alpha * Vertex Alpha"
    multiply_image_alpha_and_vertex_alpha_node = node_tree.nodes.get(
        multiply_image_alpha_and_vertex_alpha_node_name
    )
    if multiply_image_alpha_and_vertex_alpha_node is None:
        multiply_image_alpha_and_vertex_alpha_node = node_tree.nodes.new(
            "ShaderNodeMath"
        )
        multiply_image_alpha_and_vertex_alpha_node.name = (
            multiply_image_alpha_and_vertex_alpha_node_name
        )
        multiply_image_alpha_and_vertex_alpha_node.location = -800, -300
    multiply_image_alpha_and_vertex_alpha_node: bpy.types.ShaderNodeMath
    multiply_image_alpha_and_vertex_alpha_node.operation = "MULTIPLY"

    # uv map node

    uv_map_node_name = "SMH UV Map"
    uv_map_node = node_tree.nodes.get(uv_map_node_name)
    if uv_map_node is None:
        uv_map_node = node_tree.nodes.new("ShaderNodeUVMap")
        uv_map_node.name = uv_map_node_name
        uv_map_node.location = -2900, -400

    # separate uv components node

    uv_separate_node_name = "SMH Separate UV"
    uv_separate_node = node_tree.nodes.get(uv_separate_node_name)
    if uv_separate_node is None:
        uv_separate_node = node_tree.nodes.new("ShaderNodeSeparateXYZ")
        uv_separate_node.name = uv_separate_node_name
        uv_separate_node.location = -2700, -400

    # uv mirror u node

    uv_mirror_u_node_name = "SMH UV Mirror U"
    uv_mirror_u_node = node_tree.nodes.get(uv_mirror_u_node_name)
    if uv_mirror_u_node is None:
        uv_mirror_u_node = node_tree.nodes.new("ShaderNodeMath")
        uv_mirror_u_node.name = uv_mirror_u_node_name
        uv_mirror_u_node.location = -2400, 0
    uv_mirror_u_node: bpy.types.ShaderNodeMath
    uv_mirror_u_node.operation = "PINGPONG"
    uv_mirror_u_node.inputs[1].default_value = 1

    # uv mirror v node

    uv_mirror_v_node_name = "SMH UV Mirror V"
    uv_mirror_v_node = node_tree.nodes.get(uv_mirror_v_node_name)
    if uv_mirror_v_node is None:
        uv_mirror_v_node = node_tree.nodes.new("ShaderNodeMath")
        uv_mirror_v_node.name = uv_mirror_v_node_name
        uv_mirror_v_node.location = -2400, -200
    uv_mirror_v_node: bpy.types.ShaderNodeMath
    uv_mirror_v_node.operation = "PINGPONG"
    uv_mirror_v_node.inputs[1].default_value = 1

    # uv clamp u node

    uv_clamp_u_node_name = "SMH UV Clamp U"
    uv_clamp_u_node = node_tree.nodes.get(uv_clamp_u_node_name)
    if uv_clamp_u_node is None:
        uv_clamp_u_node = node_tree.nodes.new("ShaderNodeClamp")
        uv_clamp_u_node.name = uv_clamp_u_node_name
        uv_clamp_u_node.location = -2400, -500
    uv_clamp_u_node: bpy.types.ShaderNodeClamp
    uv_clamp_u_node.clamp_type = "MINMAX"
    uv_clamp_u_node.inputs["Min"].default_value = 0
    uv_clamp_u_node.inputs["Max"].default_value = 1

    # uv clamp v node

    uv_clamp_v_node_name = "SMH UV Clamp V"
    uv_clamp_v_node = node_tree.nodes.get(uv_clamp_v_node_name)
    if uv_clamp_v_node is None:
        uv_clamp_v_node = node_tree.nodes.new("ShaderNodeClamp")
        uv_clamp_v_node.name = uv_clamp_v_node_name
        uv_clamp_v_node.location = -2400, -700
    uv_clamp_v_node: bpy.types.ShaderNodeClamp
    uv_clamp_v_node.clamp_type = "MINMAX"
    uv_clamp_v_node.inputs["Min"].default_value = 0
    uv_clamp_v_node.inputs["Max"].default_value = 1

    # uv repeat type u node

    uv_repeat_type_u_name = "SMH UV Repeat Type U"
    uv_repeat_type_u = node_tree.nodes.get(uv_repeat_type_u_name)
    if uv_repeat_type_u is None:
        uv_repeat_type_u = node_tree.nodes.new("ShaderNodeValue")
        uv_repeat_type_u.name = uv_repeat_type_u_name
        uv_repeat_type_u.location = -2200, 0

    # uv repeat pick u 1 node (picks wrap/mirror)

    uv_repeat_pick1_u_name = "SMH UV Pick U 1"
    uv_repeat_pick1_u = node_tree.nodes.get(uv_repeat_pick1_u_name)
    if uv_repeat_pick1_u is None:
        uv_repeat_pick1_u = node_tree.nodes.new("ShaderNodeMapRange")
        uv_repeat_pick1_u.name = uv_repeat_pick1_u_name
        uv_repeat_pick1_u.location = -2000, -200
    uv_repeat_pick1_u.inputs["From Min"].default_value = 0
    uv_repeat_pick1_u.inputs["From Max"].default_value = 1

    # uv repeat pick u 2 node (picks pick1/clamp)

    uv_repeat_pick2_u_name = "SMH UV Pick U 2"
    uv_repeat_pick2_u = node_tree.nodes.get(uv_repeat_pick2_u_name)
    if uv_repeat_pick2_u is None:
        uv_repeat_pick2_u = node_tree.nodes.new("ShaderNodeMapRange")
        uv_repeat_pick2_u.name = uv_repeat_pick2_u_name
        uv_repeat_pick2_u.location = -1700, -200
    uv_repeat_pick2_u.inputs["From Min"].default_value = 1
    uv_repeat_pick2_u.inputs["From Max"].default_value = 2

    # uv repeat type v node

    uv_repeat_type_v_name = "SMH UV Repeat Type V"
    uv_repeat_type_v = node_tree.nodes.get(uv_repeat_type_v_name)
    if uv_repeat_type_v is None:
        uv_repeat_type_v = node_tree.nodes.new("ShaderNodeValue")
        uv_repeat_type_v.name = uv_repeat_type_v_name
        uv_repeat_type_v.location = -2200, -600

    # uv repeat pick v 1 node (picks wrap/mirror)

    uv_repeat_pick1_v_name = "SMH UV Pick V 1"
    uv_repeat_pick1_v = node_tree.nodes.get(uv_repeat_pick1_v_name)
    if uv_repeat_pick1_v is None:
        uv_repeat_pick1_v = node_tree.nodes.new("ShaderNodeMapRange")
        uv_repeat_pick1_v.name = uv_repeat_pick1_v_name
        uv_repeat_pick1_v.location = -2000, -800
    uv_repeat_pick1_v.inputs["From Min"].default_value = 0
    uv_repeat_pick1_v.inputs["From Max"].default_value = 1

    # uv repeat pick v 2 node (picks pick1/clamp)

    uv_repeat_pick2_v_name = "SMH UV Pick V 2"
    uv_repeat_pick2_v = node_tree.nodes.get(uv_repeat_pick2_v_name)
    if uv_repeat_pick2_v is None:
        uv_repeat_pick2_v = node_tree.nodes.new("ShaderNodeMapRange")
        uv_repeat_pick2_v.name = uv_repeat_pick2_v_name
        uv_repeat_pick2_v.location = -1700, -800
    uv_repeat_pick2_v.inputs["From Min"].default_value = 1
    uv_repeat_pick2_v.inputs["From Max"].default_value = 2

    # combine uv components node

    uv_combine_node_name = "SMH Combine UV"
    uv_combine_node = node_tree.nodes.get(uv_combine_node_name)
    if uv_combine_node is None:
        uv_combine_node = node_tree.nodes.new("ShaderNodeCombineXYZ")
        uv_combine_node.name = uv_combine_node_name
        uv_combine_node.location = -1500, -400

    # Node links

    # UV wrap, mirror, clamp

    node_tree.links.new(
        uv_separate_node.inputs[0],
        uv_map_node.outputs["UV"],
        verify_limits=True,
    )

    node_tree.links.new(
        uv_mirror_u_node.inputs[0],
        uv_separate_node.outputs[0],
        verify_limits=True,
    )
    node_tree.links.new(
        uv_mirror_v_node.inputs[0],
        uv_separate_node.outputs[1],
        verify_limits=True,
    )

    node_tree.links.new(
        uv_clamp_u_node.inputs[0],
        uv_separate_node.outputs[0],
        verify_limits=True,
    )
    node_tree.links.new(
        uv_clamp_v_node.inputs[0],
        uv_separate_node.outputs[1],
        verify_limits=True,
    )

    # Pick U

    node_tree.links.new(
        uv_repeat_pick1_u.inputs["Value"],
        uv_repeat_type_u.outputs[0],
        verify_limits=True,
    )
    node_tree.links.new(
        uv_repeat_pick1_u.inputs["To Min"],
        uv_separate_node.outputs[0],
        verify_limits=True,
    )
    node_tree.links.new(
        uv_repeat_pick1_u.inputs["To Max"],
        uv_mirror_u_node.outputs[0],
        verify_limits=True,
    )

    node_tree.links.new(
        uv_repeat_pick2_u.inputs["Value"],
        uv_repeat_type_u.outputs[0],
        verify_limits=True,
    )
    node_tree.links.new(
        uv_repeat_pick2_u.inputs["To Min"],
        uv_repeat_pick1_u.outputs[0],
        verify_limits=True,
    )
    node_tree.links.new(
        uv_repeat_pick2_u.inputs["To Max"],
        uv_clamp_u_node.outputs[0],
        verify_limits=True,
    )

    # Pick V

    node_tree.links.new(
        uv_repeat_pick1_v.inputs["Value"],
        uv_repeat_type_v.outputs[0],
        verify_limits=True,
    )
    node_tree.links.new(
        uv_repeat_pick1_v.inputs["To Min"],
        uv_separate_node.outputs[1],
        verify_limits=True,
    )
    node_tree.links.new(
        uv_repeat_pick1_v.inputs["To Max"],
        uv_mirror_v_node.outputs[0],
        verify_limits=True,
    )

    node_tree.links.new(
        uv_repeat_pick2_v.inputs["Value"],
        uv_repeat_type_v.outputs[0],
        verify_limits=True,
    )
    node_tree.links.new(
        uv_repeat_pick2_v.inputs["To Min"],
        uv_repeat_pick1_v.outputs[0],
        verify_limits=True,
    )
    node_tree.links.new(
        uv_repeat_pick2_v.inputs["To Max"],
        uv_clamp_v_node.outputs[0],
        verify_limits=True,
    )

    # UV output

    node_tree.links.new(
        uv_combine_node.inputs[0],
        uv_repeat_pick2_u.outputs[0],
        verify_limits=True,
    )
    node_tree.links.new(
        uv_combine_node.inputs[1],
        uv_repeat_pick2_v.outputs[0],
        verify_limits=True,
    )

    node_tree.links.new(
        image_node.inputs[0],
        uv_combine_node.outputs[0],
        verify_limits=True,
    )

    # Color

    node_tree.links.new(
        multiply_image_color_and_vertex_color_node.inputs[0],
        image_node.outputs["Color"],
        verify_limits=True,
    )
    node_tree.links.new(
        multiply_image_color_and_vertex_color_node.inputs[1],
        vertex_color_node.outputs["Color"],
        verify_limits=True,
    )
    node_tree.links.new(
        shader_node.inputs["Base Color"],
        multiply_image_color_and_vertex_color_node.outputs[0],
        verify_limits=True,
    )

    # Alpha

    node_tree.links.new(
        multiply_image_alpha_and_vertex_alpha_node.inputs[0],
        image_node.outputs["Alpha"],
        verify_limits=True,
    )
    node_tree.links.new(
        multiply_image_alpha_and_vertex_alpha_node.inputs[1],
        vertex_color_node.outputs["Alpha"],
        verify_limits=True,
    )
    node_tree.links.new(
        shader_node.inputs["Alpha"],
        multiply_image_alpha_and_vertex_alpha_node.outputs[0],
        verify_limits=True,
    )

    # Output

    node_tree.links.new(
        output_node.inputs["Surface"],
        shader_node.outputs["BSDF"],
        verify_limits=True,
    )

    # return nodes

    nodes = MaterialNodes()
    nodes.image = image_node
    nodes.uv_repeat_type_u = uv_repeat_type_u
    nodes.uv_repeat_type_v = uv_repeat_type_v

    return nodes


def on_material_image_update(self, context):
    mat: bpy.types.Material = context.material

    props: MaterialProperties = mat.simple_material_helper

    nodes = ensure_setup_and_get_nodes(mat)

    nodes.image.image = props.image

    set_uv_repeats(nodes, props)


def on_material_use_transparency_update(self, context):
    mat: bpy.types.Material = context.material

    props: MaterialProperties = mat.simple_material_helper

    if props.use_transparency:
        if props.use_blend_transparency:
            mat.blend_method = "BLEND"
            mat.use_backface_culling = True
        else:
            mat.blend_method = "CLIP"
            mat.alpha_threshold = 0.5
            mat.use_backface_culling = False
    else:
        mat.blend_method = "OPAQUE"
        mat.use_backface_culling = False


def on_material_use_blend_transparency_update(self, context):
    on_material_use_transparency_update(self, context)


def set_uv_repeats(
    nodes: MaterialNodes,
    props,  # type: MaterialProperties
):
    values = {
        "WRAP": 0,
        "MIRROR": 1,
        "CLAMP": 2,
    }
    nodes.uv_repeat_type_u.outputs[0].default_value = values[props.uv_repeat_u]
    nodes.uv_repeat_type_v.outputs[0].default_value = values[props.uv_repeat_v]


def on_material_uv_repeat_update(self, context):
    mat: bpy.types.Material = context.material

    props: MaterialProperties = mat.simple_material_helper

    nodes = ensure_setup_and_get_nodes(mat)

    set_uv_repeats(nodes, props)


class MaterialProperties(bpy.types.PropertyGroup):
    image: bpy.props.PointerProperty(
        type=bpy.types.Image,
        update=on_material_image_update,
    )
    use_transparency: bpy.props.BoolProperty(
        name="Preview Image Alpha & Vertex Alpha",
        description=(
            "Should the alpha from the image or from vertex alpha make the geometry "
            "transparent.\n"
            "Automatically toggles backface culling"
        ),
        default=False,
        update=on_material_use_transparency_update,
    )
    use_blend_transparency: bpy.props.BoolProperty(
        name="Semi-Transparent",
        description=(
            "Should the alpha be used to make the geometry partially transparent "
            "(known as alpha blend).\n"
            "If unchecked, the geometry will be either fully opaque or fully "
            "transparent, depending on if the alpha is closer to opaque or transparent "
            "(known as alpha clip).\n"
            "Automatically toggles backface culling"
        ),
        default=True,
        update=on_material_use_blend_transparency_update,
    )

    uv_repeat_u: bpy.props.EnumProperty(
        items=[
            (
                "WRAP",
                "Wrap",
                "Makes the image normally repeat along U",
                "TEXTURE",
                0,
            ),
            (
                "MIRROR",
                "Mirror",
                "Makes the image repeat along U, mirroring every other repetition",
                "MOD_MIRROR",
                1,
            ),
            (
                "CLAMP",
                "Clamp",
                "Makes the image not repeat along U, "
                "stretching the first and last columns of the image",
                "FULLSCREEN_EXIT",
                2,
            ),
        ],
        name="UV Repeat U",
        description="How to repeat the image along the U component of UVs",
        default="WRAP",
        update=on_material_uv_repeat_update,
    )
    uv_repeat_v: bpy.props.EnumProperty(
        items=[
            (
                "WRAP",
                "Wrap",
                "Makes the image normally repeat along V",
                "TEXTURE",
                0,
            ),
            (
                "MIRROR",
                "Mirror",
                "Makes the image repeat along V, mirroring every other repetition",
                "MOD_MIRROR",
                1,
            ),
            (
                "CLAMP",
                "Clamp",
                "Makes the image not repeat along V, "
                "stretching the first and last columns of the image",
                "FULLSCREEN_EXIT",
                2,
            ),
        ],
        name="UV Repeat V",
        description="How to repeat the image along the V component of UVs",
        default="WRAP",
        update=on_material_uv_repeat_update,
    )


class MaterialPanel(bpy.types.Panel):
    bl_label = "Simple Material Helper"
    # bl_idname is set in register()
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context):
        mat: Optional[bpy.types.Material] = context.material
        return mat is not None

    def draw(self, context):
        layout = self.layout

        mat: bpy.types.Material = context.material
        props: MaterialProperties = mat.simple_material_helper

        layout.label(text="Image:")
        layout.template_ID(props, "image", open="image.open")

        if props.use_transparency:
            box = layout.box()
            box.prop(props, "use_transparency")
            box.prop(props, "use_blend_transparency")
        else:
            layout.prop(props, "use_transparency")

        layout.prop(mat, "use_backface_culling")

        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(props, "uv_repeat_u")
        layout.prop(props, "uv_repeat_v")


class Config:
    # Not saved
    register_params_path: Path = None
    should_restart = False

    # Saved
    use_own_panel = False

    def read(self):
        try:
            with self.register_params_path.open() as f:
                data = json.load(f)
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            pass
        else:
            self.use_own_panel = data.get("use_own_panel", self.use_own_panel)

    def write(self):
        data = {
            "use_own_panel": self.use_own_panel,
        }
        with self.register_params_path.open("w") as f:
            json.dump(data, f)


CONFIG = Config()


def on_use_own_panel_update(self, context):
    CONFIG.should_restart = True
    CONFIG.use_own_panel = self.use_own_panel
    CONFIG.write()


class AddonProperties(bpy.types.AddonPreferences):
    bl_idname = __name__

    use_own_panel: bpy.props.BoolProperty(
        name="Separate Panel",
        description=(
            "Should the panel be its own separated and draggable panel.\n"
            "By default the panel is attached to the top of the material properties.\n"
            "(requires restarting Blender to apply changes)"
        ),
        default=False,
        update=on_use_own_panel_update,
    )

    def draw(self, context):
        layout = self.layout
        if CONFIG.should_restart:
            layout.alert = True
            layout.label(text="Restart Blender to apply changes", icon="ERROR")
            layout.alert = False
        layout.prop(self, "use_own_panel")


classes = (
    AddonProperties,
    MaterialProperties,
    MaterialPanel,
)


def register():
    CONFIG.register_params_path = (
        Path(bpy.utils.user_resource("SCRIPTS", "addons"))
        / "simple_material_helper_config.json"
    )
    try:
        CONFIG.read()
    except:
        print(
            "An exception occurred when reading json config from",
            str(CONFIG.register_params_path),
        )
        traceback.print_exception()

    if CONFIG.use_own_panel:
        MaterialPanel.bl_idname = "MATERIAL_PT_simple_material_helper_own"
        MaterialPanel.bl_options.discard("HIDE_HEADER")
    else:
        MaterialPanel.bl_idname = "MATERIAL_PT_simple_material_helper_top"
        MaterialPanel.bl_options.add("HIDE_HEADER")

    for clazz in classes:
        try:
            bpy.utils.register_class(clazz)
        except:
            print("register_class failed on", clazz)
            traceback.print_exception()
    bpy.types.Material.simple_material_helper = bpy.props.PointerProperty(
        type=MaterialProperties,
    )


def unregister():
    for clazz in reversed(classes):
        try:
            bpy.utils.unregister_class(clazz)
        except:
            print("unregister_class failed on", clazz)
            traceback.print_exception()


if __name__ == "__main__":
    register()
