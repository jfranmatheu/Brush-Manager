import bpy
from bpy.types import Event, Context
from bpy.props import StringProperty, BoolProperty, EnumProperty

from ..types import AddonData, UIProps, AddonDataByMode
from brush_manager.addon_utils import Reg
from brush_manager.paths import Paths
from brush_manager.icons import new_preview
import brush_manager.types as bm_types


def get_category_items(self, context: Context):
    ui_props = UIProps.get_data(context)
    addon_data = AddonData.get_data_by_context(ui_props)
    cat_type = ui_props.ui_context_item
    if cat_type == 'BRUSH':
        cat_coll = addon_data.brush_cats
    else:
        cat_coll = addon_data.texture_cats
    return [
        (cat.uuid, cat.name, cat.name) for cat in cat_coll
    ]


@Reg.Ops.setup
class SelectAll(Reg.Ops.ACTION):
    ''' Select-Action over Active Category items. '''

    select_action: EnumProperty(
        name="Select Action",
        items=(
            ('TOGGLE', "Toggle", "Toggle Selected"),
            ('SELECT_ALL', "Select All", ""),
            ('DESELECT_ALL', "Deselect All", "")
        ),
        default='SELECT_ALL'
    )

    def get_data(self, ui_props: UIProps, bm_data: AddonDataByMode) -> bm_types.Category:
        return bm_data.brush_cats.active if ui_props.is_ctx_brush else bm_data.texture_cats.active

    def action(self, cat: bm_types.Category) -> None:
        if self.select_action == 'TOGGLE':
            for item in cat.items:
                item.select = not item.select

        elif self.select_action == 'DESELECT_ALL':
            for item in cat.items.selected:
                item.select = False

        elif self.select_action == 'SELECT_ALL':
            for item in cat.items:
                item.select = True


@Reg.Ops.setup
class SelectItem(Reg.Ops.ACTION):
    ''' Select Item (toggle like). '''

    item_uuid: StringProperty(default='', options={'HIDDEN', 'SKIP_SAVE'})

    def get_data(self, ui_props: UIProps, bm_data: AddonDataByMode) -> bm_types.Category:
        return bm_data.brush_cats.active if ui_props.is_ctx_brush else bm_data.texture_cats.active

    def action(self, cat: bm_types.Category):
        if cat is None:
            return
        if item := cat.items.get(self.item_uuid):
            item.select = not item.select

@Reg.Ops.setup
class RemoveSelectedFromActiveCategory(Reg.Ops.ACTION):
    ''' Removes all selected items from the active category. '''

    def get_data(self, ui_props: UIProps, bm_data: AddonDataByMode) -> bm_types.Category:
        return bm_data.brush_cats.active if ui_props.is_ctx_brush else bm_data.texture_cats.active

    def action(self, cat: bm_types.Category) -> None:
        for item in cat.items.selected:
            cat.items.remove(item.uuid, perma_remove=True)


@Reg.Ops.setup
class MoveSelectedToCategory(Reg.Ops.INVOKE_PROPS_POPUP):
    ''' Move Selected items from the active category to the specified category. '''

    select_category : EnumProperty(
        name="Select a Category",
        items=get_category_items
    )

    def get_data(self, ui_props: UIProps, addon_data: AddonDataByMode) -> bm_types.Category:
        if ui_props.is_ctx_brush:
            cat = addon_data.brush_cats.active
            target_cat = addon_data.get_brush_cat(self.select_category)
        else:
            cat = addon_data.texture_cats.active
            target_cat = addon_data.get_texture_cat(self.select_category)

        if cat is None:
            return None

        return cat, target_cat

    def action(self, cat: bm_types.Category, target_cat: bm_types.Category) -> None:
        for sel_item in cat.items.selected:
            cat.items.move(sel_item.uuid, target_cat.items)
        target_cat.set_active()
        SelectAll.run(select_action='DESELECT_ALL')


@Reg.Ops.setup
class AsignIconToBrush(Reg.Ops.Import.PNG):
    brush_uuid: StringProperty(default='', options={'HIDDEN', 'SKIP_SAVE'})

    def get_data(self, _ui_props: UIProps, addon_data: AddonDataByMode) -> bm_types.Category:
        return addon_data.active_category.items.get(self.brush_uuid) if self.brush_uuid != '' else addon_data.active_brush

    def action(self, brush: bm_types.BrushItem | None) -> None:
        if brush is not None:
            brush.asign_icon(self.filepath)
