#pragma once

#include "esphome/core/component.h"
#include "esphome/core/automation.h"
#include "remote_webview.h"

namespace esphome {
namespace remote_webview {

// Automation things below
// MODIFIED: Renamed to TriggerOnFrameUpdateAction to match what it does. 
// Removed TEMPLATABLE_VALUE(bool, state) as it requires no arguments now.
template<typename... Ts> class TriggerOnFrameUpdateAction : public Action<Ts...> {
 public:
  explicit TriggerOnFrameUpdateAction(RemoteWebView *ea) : ea_(ea) {}

  void play(Ts... x) override {
    // MODIFIED: We just call our component's trigger method directly.
    this->ea_->trigger_on_frame_update();
  }

 protected:
  RemoteWebView *ea_;
};
/*template<typename... Ts> class OnFrameUpdateSetStateAction : public Action<Ts...> {
 public:
  explicit OnFrameUpdateSetStateAction(RemoteWebView *ea) : ea_(ea) {}
  TEMPLATABLE_VALUE(bool, state)

  void play(Ts... x) override {
    auto val = this->state_.value(x...);
    this->ea_->set_state(val);
  }

 protected:
  RemoteWebView *ea_;
};*/

// Trying to cull the condition part of the automation since we don't need that
/*
template<typename... Ts> class OnFrameUpdateCondition : public Condition<Ts...> {
 public:
  OnFrameUpdateCondition(RemoteWebView *parent, bool state) : parent_(parent), state_(state) {}
  bool check(Ts... x) override { return this->parent_->state == this->state_; }

 protected:
  RemoteWebView *parent_;
  bool state_;
}; */

// MODIFIED: Renamed to OnFrameUpdateTrigger. Changed 'Trigger<bool>' to 'Trigger<>' 
// because we don't need to pass a boolean along with the trigger anymore.
class OnFrameUpdateTrigger : public Trigger<> {
 public:
  explicit OnFrameUpdateTrigger(RemoteWebView *parent) {
    // MODIFIED: Use our new parameterless callback manager.
    parent->add_on_frame_update_callback([this]() { this->trigger(); });
  }
};
/*class OnFrameUpdateStateTrigger : public Trigger<bool> {
 public:
  explicit OnFrameUpdateStateTrigger(RemoteWebView *parent) {
    parent->add_on_state_callback([this](bool state) { this->trigger(state); });
  }
};*/

}  // namespace remote_webview
}  // namespace esphome
