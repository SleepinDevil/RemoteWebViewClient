#pragma once

#include "esphome/core/component.h"
#include "esphome/core/automation.h"
#include "remote_webview.h"

namespace esphome {
namespace remote_webview {

template<typename... Ts> class OnFrameUpdateSetStateAction : public Action<Ts...> {
 public:
  explicit OnFrameUpdateSetStateAction(RemoteWebView *ea) : ea_(ea) {}
  TEMPLATABLE_VALUE(bool, state)

  void play(Ts... x) override {
    auto val = this->state_.value(x...);
    this->ea_->set_state(val);
  }

 protected:
  RemoteWebView *ea_;
};

template<typename... Ts> class OnFrameUpdateCondition : public Condition<Ts...> {
 public:
  OnFrameUpdateCondition(RemoteWebView *parent, bool state) : parent_(parent), state_(state) {}
  bool check(Ts... x) override { return this->parent_->state == this->state_; }

 protected:
  RemoteWebView *parent_;
  bool state_;
};

class OnFrameUpdateStateTrigger : public Trigger<bool> {
 public:
  explicit OnFrameUpdateStateTrigger(RemoteWebView *parent) {
    parent->add_on_state_callback([this](bool state) { this->trigger(state); });
  }
};

}  // namespace remote_webview
}  // namespace esphome
