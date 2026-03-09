> [!IMPORTANT]
>
> **_About this fork_**
>
> The modifications done in my server fork are: 
> 1. Provide an "on_frame_update" event on the remote_webview whenever the display frame gets updated, this can be used to trigger a brightness script for example. This triggers a maximum of once every second.
> 2. Provide a "current_url_sensor" sensor on the remote_webview that processes Packet #6 that my server code sends. You need to have my server code running on your docker container for this sensor to get populated, otherwise it will remain "unknown".

# 1. on_frame_update event

All you need to do to trial this is to point your Docker Compose file at this GitHub repo (full example code below from Strange-V's hard work).

If you find any bugs please let me know. I might be able to fix things, but if you have a fix yourself, please put in a PR.

```yaml
external_components:
  #- source: github://strange-v/RemoteWebViewClient@main
  - source: github://SleepinDevil/RemoteWebViewClient@current-url-packet #use @main instead if you don't want modification #2 below as well
    refresh: 0s
    components: [ remote_webview ]

remote_webview:
  # other settings omitted
  on_frame_update:
    then:
      - script.execute: inactivity_timer

script:
  - id: inactivity_timer
    mode: restart
    then:
      - light.turn_on: 
          id: back_light
          brightness: !lambda return int ( id (sd_backlight_brightness).state )/ 100.0; #use whatever id you have for your brightness slider
          transition_length: 0.5s
      - delay: 10s
      - light.dim_relative:
          id: back_light
          relative_brightness: -40%
          transition_length: 3s
          brightness_limits:
            min_brightness: 30%
```


# 2. Packet #6 processing sensor from my server

You need to be running my server instance for this too: https://github.com/SleepinDevil/RemoteWebViewServer

This modification allows the user to know what webpage URL the display is currently showing. This allows automations to temporarily take over and show a different URL on the display and then revert back to the previous URL the display was on. This is just a nice-ity and nothing more.

If you build your ESP32 without my server code running on your Docker instance, then this sensor will remain on "unknown"

```yaml
external_components:
  #- source: github://strange-v/RemoteWebViewClient@main
  - source: github://SleepinDevil/RemoteWebViewClient@current-url-packet #use @main instead if you don't want modification #2 below as well
    refresh: 0s
    components: [ remote_webview ]

remote_webview:
  # other settings omitted
  current_url_sensor:
    id: current_url_sensor_id
    name: "Remote Display Current URL"
    on_value:
      - logger.log:
          format: "The screen just navigated to: %s"
          args: [ 'x.c_str()' ]
```

# My full ESP32 configuration if you want easy copy pasta

Yes I have also experimented with the JPEG Decoder optimisations, I believe my optimisations are about 10-15% faster on average from my testing so far.

You probably need to Clean Build Files before compiling this.

```yaml
substitutions:
  initial_url: "http://192.168.0.75:8123/remote-displays"  #this should be the URL to your Home Assistant dashboard you want to display

esphome:
  name: "webview-display-1"
  friendly_name: Webview-Display-1
  platformio_options:
    board_build.flash_mode: dio
  on_boot:
    priority: -100.0
    then:
      - delay: 5s
      - light.turn_on:
          id: back_light
          brightness: !lambda return int( id(sd_backlight_brightness).state )/ 100.0;

esp32:
  board: esp32-s3-devkitc-1
  variant: esp32s3
  flash_size: 16MB
  framework:
    type: esp-idf
    sdkconfig_options:
      COMPILER_OPTIMIZATION_SIZE: "y"
      CONFIG_ESP32S3_DEFAULT_CPU_FREQ_240: "y"
      CONFIG_ESP32S3_DATA_CACHE_64KB: "y"
      CONFIG_ESP32S3_DATA_CACHE_LINE_64B: "y"
      CONFIG_SPIRAM_FETCH_INSTRUCTIONS: "y"
      CONFIG_SPIRAM_RODATA: "y"
    components:
      - name: "espressif/esp_websocket_client"
        ref: 1.5.0
      - name: "bitbank2/jpegdec"
        source: https://github.com/SleepinDevil/jpegdec-esphome
        # yes I have also been experimenting with some optimisations on the JPEG Decoder
        #source: https://github.com/strange-v/jpegdec-esphome

psram:
  mode: octal
  speed: 80MHz

external_components:
  #- source: github://strange-v/RemoteWebViewClient@main
  - source: github://SleepinDevil/RemoteWebViewClient@current-url-packet
    refresh: 0s
    components: [ remote_webview ]

logger:
  hardware_uart: UART0

api:
  #encryption:
  #  key: "XXXXXXXXX"

ota:
  - platform: esphome
    password: !secret ota_password
    on_begin: # prevent screen flickering during OTA
      - light.turn_off:
          id: back_light
          transition_length: 0s
      - lambda: "id(back_light).loop();"

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password


switch:
  - platform: gpio
    name: Relay 1
    pin:
      number: GPIO40
      inverted: true
  - platform: gpio
    name: Relay 2
    pin:
      number: GPIO2
      inverted: true
  - platform: gpio
    name: Relay 3
    pin:
      number: GPIO1
      inverted: true

button:
  - platform: template
    name: "Test on_frame_update trigger"
    on_press:
      then:
      - remote_webview.trigger_on_frame_update:
          id: rwv
    entity_category: "diagnostic" 

captive_portal:
    
spi:
  clk_pin: GPIO48
  mosi_pin: GPIO47

i2c:
  - id: bus_a
    sda: GPIO19
    scl:
      number: 45
      ignore_strapping_warning: true

number:
  - platform: template
    name: Backlight Brightness
    id: sd_backlight_brightness
    optimistic: true
    restore_value: true
    min_value: 30
    max_value: 100
    initial_value: 70
    step: 5
    set_action:
      then:
      - light.turn_on:
          id: back_light
          brightness: !lambda return int(x)/ 100.0;
      - script.execute: inactivity_timer

display:
  - platform: st7701s
    show_test_card: False
    update_interval: never
    auto_clear_enabled: False
    spi_mode: MODE3
    data_rate: 2MHz
    color_order: RGB
    invert_colors: False
    dimensions:
      width: 480
      height: 480
    cs_pin: 39
    de_pin: 18
    hsync_pin: 16
    vsync_pin: 17
    pclk_pin: 21
    pclk_frequency: 12MHz
    pclk_inverted: False
    hsync_pulse_width: 8
    hsync_front_porch: 10
    hsync_back_porch: 20
    vsync_pulse_width: 8
    vsync_front_porch: 10
    vsync_back_porch: 10
    init_sequence:
      - 1
      - [0xFF, 0x77, 0x01, 0x00, 0x00, 0x10]
      - [0xCD, 0x00]
    data_pins:
      red: [11, 12, 13, 14, 0]
      green: [8, 20, 3, 46, 9, 10]
      blue: [4, 5, 6, 7, 15]

touchscreen:
  platform: gt911
  transform:
    mirror_x: false
    mirror_y: false
  i2c_id: bus_a
  on_touch:
    then:
      - script.execute: inactivity_timer

output:
  - platform: ledc
    pin: GPIO38
    id: backlight_pwm
    frequency: 150Hz
    min_power: 0.01
    zero_means_zero: true

light:
  - platform: monochromatic
    output: backlight_pwm
    name: "Display Backlight"
    id: back_light
    restore_mode: ALWAYS_ON
    default_transition_length: 2s

remote_webview:
  id: rwv
  server: 192.168.0.57:8081 # this is the URL for the server instance
  url: ${initial_url}  # set url: "self-test" to initiate the self-test
  #url: "self-test"
  full_frame_tile_count: 2
  tile_size: 32
  full_frame_every: 60
  min_frame_interval: 60 
  # this was 66 without the unrolling optimisations, now it can be as low as 59 based on new test - this is for 85 jpeg_quality
  # for 95 jpeg_quality, we can pull it off with 64ms it looks like, so try 65 for the interval
  max_bytes_per_msg: 61440
  jpeg_quality: 95
  on_frame_update:
    then:
      - script.execute: inactivity_timer
  current_url_sensor:
    id: current_url_sensor_id
    name: "Remote Display Current URL"
    on_value:
      - logger.log:
          format: "The screen just navigated to: %s"
          args: [ 'x.c_str()' ]

text:
  - platform: template
    id: rwv_url
    name: "Load New URL"
    optimistic: true
    restore_value: false
    mode: TEXT
    min_length: 1
    initial_value: ${initial_url}
    set_action:
      - lambda: |-
          if (!id(rwv).open_url(std::string(x.c_str()))) {
            id(rwv).set_url(std::string(x.c_str()));
            ESP_LOGI("remote_webview", "URL queued (not connected): %s", x.c_str());
          }

script:
  - id: inactivity_timer
    mode: restart
    then:
      - light.turn_on: 
          id: back_light
          brightness: !lambda return int ( id (sd_backlight_brightness).state )/ 100.0;
          transition_length: 0.5s
      - delay: 10s
      - light.dim_relative:
          id: back_light
          relative_brightness: -40%
          transition_length: 3s
          brightness_limits:
            min_brightness: 30%
  - id: about_black_stuck
    mode: restart
    then:
      - delay: 30s
      - if: 
          condition:
            lambda: 'return id(current_url_sensor_id).state == "unknown";'
          then:
            - logger.log: "Current displayed URL is 'Unknown', let's attempt to set it again."
            - lambda: |-
                if ( !id(rwv).open_url( "${initial_url}" ) ) {
                  id(rwv).set_url("${initial_url}");
                  ESP_LOGI("remote_webview", "URL queued (not connected): ${initial_url}");
                }
```


# Original description from Strange-V below

[![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner-direct-single.svg)](https://stand-with-ukraine.pp.ua)

# Remote WebView Client

![Guition-ESP32-S3-4848S040 running Remote WebView](/images/image-001.jpg)

[Demo video](https://youtu.be/rD2aYUUrv5o)

This is a client that connects to [Remote WebView Server](https://github.com/strange-v/RemoteWebViewServer) — a headless browser that renders target web pages (e.g., Home Assistant dashboards) and streams them as image tiles over WebSocket to lightweight clients (ESP32 displays).

## ESPHome component

The latest version of the client is implemented as an ESPHome external component, which greatly simplifies installation and configuration for end users. It leverages the display and touchscreen components to render images and handle touch input.

### Configuration example (Guition-ESP32-S3-4848S040)

```yaml
esphome:
  name: esp32-4848s040-t1
  friendly_name: ESP32-4848S040-T1
  platformio_options:
    board_build.flash_mode: dio

esp32:
  board: esp32-s3-devkitc-1
  variant: esp32s3
  flash_size: 16MB
  framework:
    type: esp-idf
    sdkconfig_options:
      COMPILER_OPTIMIZATION_SIZE: y
      CONFIG_ESP32S3_DEFAULT_CPU_FREQ_240: "y"
      CONFIG_ESP32S3_DATA_CACHE_64KB: "y"
      CONFIG_ESP32S3_DATA_CACHE_LINE_64B: "y"
      CONFIG_SPIRAM_FETCH_INSTRUCTIONS: y
      CONFIG_SPIRAM_RODATA: y
    components:
      - name: "espressif/esp_websocket_client"
        ref: 1.5.0
      - name: "bitbank2/jpegdec"
        source: https://github.com/strange-v/jpegdec-esphome

psram:
  mode: octal
  speed: 80MHz

external_components:
  - source: github://strange-v/RemoteWebViewClient@main
    refresh: 0s
    components: [ remote_webview ]

logger:
  hardware_uart: UART0

api:
  encryption:
    key: "XXXXXXXXX"

ota:
  - platform: esphome
    password: "XXXXXXXXX"

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

captive_portal:
    
spi:
  clk_pin: GPIO48
  mosi_pin: GPIO47

i2c:
  - id: bus_a
    sda: GPIO19
    scl: GPIO45

display:
  - platform: st7701s
    show_test_card: False
    update_interval: never
    auto_clear_enabled: False
    spi_mode: MODE3
    data_rate: 2MHz
    color_order: RGB
    invert_colors: False
    dimensions:
      width: 480
      height: 480
    cs_pin: 39
    de_pin: 18
    hsync_pin: 16
    vsync_pin: 17
    pclk_pin: 21
    pclk_frequency: 12MHz
    pclk_inverted: False
    hsync_pulse_width: 8
    hsync_front_porch: 10
    hsync_back_porch: 20
    vsync_pulse_width: 8
    vsync_front_porch: 10
    vsync_back_porch: 10
    init_sequence:
      - 1
      - [0xFF, 0x77, 0x01, 0x00, 0x00, 0x10]
      - [0xCD, 0x00]
    data_pins:
      red:
        - GPIO11
        - GPIO12
        - GPIO13
        - GPIO14
        - GPIO0
      green:
        - GPIO8
        - GPIO20
        - GPIO3
        - GPIO46
        - GPIO9
        - GPIO10
      blue:
        - GPIO4
        - GPIO5
        - GPIO6
        - GPIO7
        - GPIO15

touchscreen:
  platform: gt911
  transform:
    mirror_x: false
    mirror_y: false
  i2c_id: bus_a

output:
  - platform: ledc
    pin: GPIO38
    id: backlight_pwm

light:
  - platform: monochromatic
    output: backlight_pwm
    name: "Display Backlight"
    id: back_light
    restore_mode: ALWAYS_ON

remote_webview:
  id: rwv
  server: 172.16.0.252:8081
  url: http://172.16.0.252:8123/dashboard-mobile/0  # set url: "self-test" to initiate the self-test
  full_frame_tile_count: 1
  max_bytes_per_msg: 61440
  jpeg_quality: 85

text:
  - platform: template
    id: rwv_url
    name: "URL"
    optimistic: true
    restore_value: false
    mode: TEXT
    min_length: 1
    set_action:
      - lambda: |-
          if (!id(rwv).open_url(std::string(x.c_str()))) {
            id(rwv).set_url(std::string(x.c_str()));
            ESP_LOGI("remote_webview", "URL queued (not connected): %s", x.c_str());
          }

```

### Supported Parameters

| YAML key                | Type      | Required | Example                          | Description |
|-------------------------|-----------|:--------:|----------------------------------|-------------|
| `display_id`            | id        | ❌       | `panel`                           | Display to draw on. Optional, if only one display is defined in the YAML.|
| `touchscreen_id`        | id        | ❌       | `touch`                           | Touch input source. Optional, if only one touchscreen is defined in the YAML. |
| `server`                | string    | ✅       | `172.16.0.252:8081`              | WebSocket server address. Must be `hostname_or_IP:port`. |
| `url`                   | string    | ✅       | `http://…/dashboard`             | Page to open on connect. |
| `device_id`             | string    | ❌       | `"my-device"` or auto (`esp32-<mac>`) | Identifier used by the server. If not set, the component derives `esp32-<mac>` from the chip MAC and still sends it. |
| `tile_size`             | int       | ❌       | `32`                              | Tile edge size in pixels. Helps the server choose tile packing; it’s best to keep it a multiple of 16. |
| `full_frame_tile_count` | int       | ❌       | `4`                               | Number of tiles the server should use for full-frame updates. |
| `full_frame_area_threshold` | float | ❌       | `0.50`                            | Area delta (fraction of screen) above which the server should send a full frame. |
| `full_frame_every`      | int       | ❌       | `50`                              | Force a full-frame update every N frames (0 disables). |
| `every_nth_frame`       | int       | ❌       | `1`                               | Frame-rate divider. Server should send only every Nth frame. |
| `min_frame_interval`    | int (ms)  | ❌       | `80`                              | Minimum time between frames on the wire, in milliseconds. |
| `jpeg_quality`          | int       | ❌       | `85`                              | JPEG quality hint for the server’s encoder. |
| `max_bytes_per_msg`     | int (B)   | ❌       | `14336` or `61440`                | Upper bound for a single WS binary message. |
| `big_endian`            | bool      | ❌       | `true` or `false`                 | Use big-endian RGB565 pixel order for JPEG output (set false for little-endian panels). Default is `true`. |
| `rotation`              | int       | ❌       | 0, 90, 180, 270                   | Enables software rotation for both the display and touchscreen. |

## Recommendations

- **full_frame_tile_count** set to 1 is the most efficient way to do a full-screen update; use it if your network/device memory allows it.
- **every_nth_frame** must be 1 if you don’t want to miss changes (though increasing it may reduce server load). I recommend keeping it set to 1.
- **min_frame_interval** should be slightly larger than the render time reported by the self-test (set `self-test` as a url parameter in the YAML).
- **max_bytes_per_msg** should be larger than your maximum tile size (full-frame or partial).
- **jpeg_quality** — lower values encode faster and reduce bandwidth (but increase artifacts). Start at **85**, drop toward **70–75** if you need speed.
- **big_endian** — defaults to **true**. If colors look wrong (swapped/tinted), set `big_endian: false` for panels that require little-endian RGB565.
- **Red tile / red screen** — this indicates a tile payload exceeded `max_bytes_per_msg`. Increase `max_bytes_per_msg` or reduce tile size/JPEG quality so each tile fits.

## No on-screen keyboard

There’s no on-screen keyboard; you’ll need to [use Chrome DevTools](https://github.com/strange-v/RemoteWebViewServer#accessing-the-servers-tab-with-chrome-devtools) for any required input.
