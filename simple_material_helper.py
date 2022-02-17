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

import typing

if typing.TYPE_CHECKING:
    from typing import (
        Optional,
    )


class MaterialNodes:
    image: bpy.types.ShaderNodeTexImage


def ensure_setup_and_get_nodes(material: bpy.types.Material):
    node_tree = material.node_tree

    # ensure vertex colors data exists

    for mesh in bpy.data.meshes:
        mesh: bpy.types.Mesh
        if material in mesh.materials.values():
            if mesh.vertex_colors.active is None:
                mesh.vertex_colors.new(do_init=False)

    # output node

    output_node_name = "SMH Output Material"
    output_node = node_tree.nodes.get(output_node_name)
    if output_node is None:
        output_node = node_tree.nodes.new("ShaderNodeOutputMaterial")
        output_node.name = output_node_name

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

    shader_node.inputs["Specular"].default_value = 0

    # image node

    image_node_name = "SMH Image Texture"
    image_node = node_tree.nodes.get(image_node_name)
    if image_node is None:
        image_node = node_tree.nodes.new("ShaderNodeTexImage")
        image_node.name = image_node_name

    # vertex color node

    vertex_color_node_name = "SMH Vertex Color"
    vertex_color_node = node_tree.nodes.get(vertex_color_node_name)
    if vertex_color_node is None:
        vertex_color_node = node_tree.nodes.new("ShaderNodeVertexColor")
        vertex_color_node.name = vertex_color_node_name

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
    multiply_image_alpha_and_vertex_alpha_node: bpy.types.ShaderNodeMath
    multiply_image_alpha_and_vertex_alpha_node.operation = "MULTIPLY"

    # links

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

    node_tree.links.new(
        output_node.inputs["Surface"],
        shader_node.outputs["BSDF"],
        verify_limits=True,
    )

    # return nodes

    nodes = MaterialNodes()
    nodes.image = image_node

    return nodes


def on_material_image_update(self, context):
    mat: bpy.types.Material = context.material

    props: MaterialProperties = mat.simple_material_helper

    nodes = ensure_setup_and_get_nodes(mat)

    nodes.image.image = props.image


class MaterialProperties(bpy.types.PropertyGroup):
    image: bpy.props.PointerProperty(
        type=bpy.types.Image,
        update=on_material_image_update,
    )


class MaterialPanel(bpy.types.Panel):
    bl_label = "Simple Material Helper"
    bl_idname = "MATERIAL_PT_simple_material_helper"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

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


classes = (
    MaterialProperties,
    MaterialPanel,
)


def register():
    for clazz in classes:
        try:
            bpy.utils.register_class(clazz)
        except:
            print("register_class failed on", clazz)
    bpy.types.Material.simple_material_helper = bpy.props.PointerProperty(
        type=MaterialProperties,
    )


def unregister():
    for clazz in reversed(classes):
        try:
            bpy.utils.unregister_class(clazz)
        except:
            print("unregister_class failed on", clazz)


if __name__ == "__main__":
    register()
