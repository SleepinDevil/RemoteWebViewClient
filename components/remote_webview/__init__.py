import re
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import automation
from esphome.components import display, touchscreen
from esphome.components.display import validate_rotation
from esphome.const import CONF_ID, CONF_DISPLAY_ID, CONF_URL, CONF_ROTATION, CONF_STATE, CONF_TRIGGER_ID


CONF_DEVICE_ID = "device_id"
CONF_TOUCHSCREEN_ID = "touchscreen_id"
CONF_SERVER = "server"
CONF_TILE_SIZE = "tile_size"
CONF_FULL_FRAME_TILE_COUNT = "full_frame_tile_count"
CONF_FULL_FRAME_AREA_THRESHOLD = "full_frame_area_threshold"
CONF_FULL_FRAME_EVERY = "full_frame_every"
CONF_EVERY_NTH_FRAME = "every_nth_frame"
CONF_MIN_FRAME_INTERVAL = "min_frame_interval"
CONF_JPEG_QUALITY = "jpeg_quality"
CONF_MAX_BYTES_PER_MSG = "max_bytes_per_msg"
CONF_BIG_ENDIAN = "big_endian"

CONF_ON_FRAME_UPDATE = "on_frame_update"

_SERVER_RE = re.compile(
    r"^(?P<host>[A-Za-z0-9](?:[A-Za-z0-9\-\.]*[A-Za-z0-9])?)\:(?P<port>\d{1,5})$"
)

AUTO_LOAD = []
DEPENDENCIES = ["display"]

def validate_host_port(value):
    s = cv.string_strict(value).strip()
    m = _SERVER_RE.match(s)
    if not m:
        raise cv.Invalid("server must be in 'host:port' format (no IPv6, no trailing colon)")

    host = m.group("host")
    port = int(m.group("port"), 10)

    if not (1 <= port <= 65535):
        raise cv.Invalid("port must be between 1 and 65535")

    return f"{host}:{port}"

ns = cg.esphome_ns.namespace("remote_webview")
RemoteWebView = ns.class_("RemoteWebView", cg.Component)

# on_frame_update automation items
# Actions
OnFrameUpdateSetStateAction = ns.class_(
    "OnFrameUpdateSetStateAction", automation.Action
)
# Conditions
# Culling conditions because we only have a simple trigger on our automation
#OnFrameUpdateCondition = ns.class_(
#    "OnFrameUpdateCondition", automation.Condition
#)
# Triggers
OnFrameUpdateStateTrigger = ns.class_(
    "OnFrameUpdateStateTrigger", automation.Trigger.template(bool)
)

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(RemoteWebView),
        cv.GenerateID(CONF_DISPLAY_ID): cv.use_id(display.Display),
        cv.GenerateID(CONF_TOUCHSCREEN_ID): cv.use_id(touchscreen.Touchscreen),
        cv.Required(CONF_SERVER): validate_host_port,
        cv.Required(CONF_URL): cv.string,

        cv.Optional(CONF_DEVICE_ID): cv.string,
        cv.Optional(CONF_TILE_SIZE): cv.int_,
        cv.Optional(CONF_FULL_FRAME_TILE_COUNT): cv.int_,
        cv.Optional(CONF_FULL_FRAME_AREA_THRESHOLD): cv.float_,
        cv.Optional(CONF_FULL_FRAME_EVERY): cv.int_,
        cv.Optional(CONF_EVERY_NTH_FRAME): cv.int_,
        cv.Optional(CONF_MIN_FRAME_INTERVAL): cv.int_,
        cv.Optional(CONF_JPEG_QUALITY): cv.int_,
        cv.Optional(CONF_MAX_BYTES_PER_MSG): cv.int_,
        cv.Optional(CONF_BIG_ENDIAN): cv.boolean,
        cv.Optional(CONF_ROTATION): validate_rotation,

        
        cv.Optional(CONF_ON_FRAME_UPDATE): automation.validate_automation(
            {
                cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(OnFrameUpdateStateTrigger),
            }
        ),
    }
).extend(cv.COMPONENT_SCHEMA)

REMOTEWEBVIEW_ACTION_SCHEMA = cv.maybe_simple_value(
    {
        cv.Required(CONF_ID): cv.use_id(RemoteWebView),
        cv.Required(CONF_STATE): cv.boolean,
    },
    key=CONF_STATE,
)

# another condition automation element that we don't need
"""
REMOTEWEBVIEW_CONDITION_SCHEMA = automation.maybe_simple_id(
    {
        cv.Required(CONF_ID): cv.use_id(RemoteWebView),
    }
)
"""

@automation.register_action(
    "remote_webview.frame_update_trigger",
    OnFrameUpdateSetStateAction,
    REMOTEWEBVIEW_ACTION_SCHEMA,
)
async def remote_webview_frame_update_trigger_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, paren)
    cg.add(var.frame_update_trigger(config[CONF_STATE]))
    return var

# Trying to cull extra things in the Automation that might not be necessary
"""
@automation.register_condition(
    "remote_webview.component_on",
    OnFrameUpdateCondition,
    REMOTEWEBVIEW_CONDITION_SCHEMA,
)
async def remote_webview_component_on_to_code(
    config, condition_id, template_arg, args
):
    paren = await cg.get_variable(config[CONF_ID])
    return cg.new_Pvariable(condition_id, template_arg, paren, True)


@automation.register_condition(
    "remote_webview.component_off",
    OnFrameUpdateCondition,
    REMOTEWEBVIEW_CONDITION_SCHEMA,
)
async def remote_webview_component_off_to_code(
    config, condition_id, template_arg, args
):
    paren = await cg.get_variable(config[CONF_ID])
    return cg.new_Pvariable(condition_id, template_arg, paren, False)
"""

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])

    disp = await cg.get_variable(config[CONF_DISPLAY_ID])
    cg.add(var.set_display(disp))
    cg.add(var.set_server(config[CONF_SERVER]))
    cg.add(var.set_url(config[CONF_URL]))

    if CONF_TOUCHSCREEN_ID in config:
        ts = await cg.get_variable(config[CONF_TOUCHSCREEN_ID])
        cg.add(var.set_touchscreen(ts))

    if CONF_DEVICE_ID in config:
        cg.add(var.set_device_id(config[CONF_DEVICE_ID]))
    if CONF_TILE_SIZE in config:
        cg.add(var.set_tile_size(config[CONF_TILE_SIZE]))
    if CONF_FULL_FRAME_TILE_COUNT in config:
        cg.add(var.set_full_frame_tile_count(config[CONF_FULL_FRAME_TILE_COUNT]))
    if CONF_FULL_FRAME_AREA_THRESHOLD in config:
        cg.add(var.set_full_frame_area_threshold(config[CONF_FULL_FRAME_AREA_THRESHOLD]))
    if CONF_FULL_FRAME_EVERY in config:
        cg.add(var.set_full_frame_every(config[CONF_FULL_FRAME_EVERY]))
    if CONF_EVERY_NTH_FRAME in config:
        cg.add(var.set_every_nth_frame(config[CONF_EVERY_NTH_FRAME]))
    if CONF_MIN_FRAME_INTERVAL in config:
        cg.add(var.set_min_frame_interval(config[CONF_MIN_FRAME_INTERVAL]))
    if CONF_JPEG_QUALITY in config:
        cg.add(var.set_jpeg_quality(config[CONF_JPEG_QUALITY]))
    if CONF_MAX_BYTES_PER_MSG in config:
        cg.add(var.set_max_bytes_per_msg(config[CONF_MAX_BYTES_PER_MSG]))
    if CONF_BIG_ENDIAN in config:
        cg.add(var.set_big_endian(config[CONF_BIG_ENDIAN]))
    if CONF_ROTATION in config:
        cg.add(var.set_rotation(config[CONF_ROTATION]))


    await cg.register_component(var, config)

    for conf in config.get(CONF_ON_FRAME_UPDATE, []):
        trigger = cg.new_Pvariable(conf[CONF_TRIGGER_ID], var)
        await automation.build_automation(trigger, [(bool, "x")], conf)


