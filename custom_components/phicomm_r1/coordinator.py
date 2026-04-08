"""Coordinator for Phicomm R1 integration."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, field, replace
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PhicommR1ApiClient, PhicommR1ApiError
from .const import PROTOCOL_WS_NATIVE

_LOGGER = logging.getLogger(__name__)

_CHAT_BUTTON_ENABLED_STATES = {
    "ready",
    "online",
    "active",
    "available",
    "idle",
    "standby",
    "connecting",
    "listening",
    "thinking",
    "speaking",
}
_CHAT_BUTTON_DISABLED_STATES = {
    "unavailable",
    "offline",
    "error",
    "failed",
    "disabled",
    "disconnected",
}


def _suy_ra_chat_button_enabled(state_value: Any) -> bool | None:
    """Infer chat button availability from normalized chat state."""
    if state_value is None:
        return None

    normalized = str(state_value).strip().lower()
    if not normalized:
        return None

    if normalized in _CHAT_BUTTON_ENABLED_STATES:
        return True
    if normalized in _CHAT_BUTTON_DISABLED_STATES:
        return False
    return None


@dataclass(slots=True)
class PhicommR1Status:
    """Aggregated speaker status."""

    model: str | None = None
    playback_state: str | None = None
    volume_current: int | None = None
    volume_min: int | None = None
    volume_max: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    aibox_playback: dict[str, Any] = field(default_factory=dict)
    wake_word: dict[str, Any] = field(default_factory=dict)
    custom_ai: dict[str, Any] = field(default_factory=dict)
    chat_state: dict[str, Any] = field(default_factory=dict)
    led_state: dict[str, Any] = field(default_factory=dict)
    audio_state: dict[str, Any] = field(default_factory=dict)

    @property
    def volume_level(self) -> float | None:
        """Volume normalized to 0..1."""
        if self.volume_current is None or self.volume_min is None or self.volume_max is None:
            return None
        spread = self.volume_max - self.volume_min
        if spread <= 0:
            return 0.0
        return max(0.0, min(1.0, (self.volume_current - self.volume_min) / spread))

    @property
    def is_muted(self) -> bool | None:
        """Best-effort mute state from volume."""
        if self.volume_current is None:
            return None
        return self.volume_current <= 0


class PhicommR1Coordinator(DataUpdateCoordinator[PhicommR1Status]):
    """Coordinates periodic state updates from API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: PhicommR1ApiClient,
        scan_interval: timedelta,
        use_media_dispatch: bool,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Phicomm R1",
            update_interval=scan_interval,
        )
        self.client = client
        self._use_media_dispatch = use_media_dispatch
        self.client.dang_ky_callback_playback_aibox(self._async_xu_ly_cap_nhat_playback_aibox)
        hass.async_create_task(self.client.async_bat_dau_lang_nghe_playback_aibox())

    async def async_shutdown(self) -> None:
        """Detach live listeners owned by this coordinator."""
        self.client.huy_callback_playback_aibox(self._async_xu_ly_cap_nhat_playback_aibox)

    async def _async_xu_ly_cap_nhat_playback_aibox(self, playback: dict[str, Any]) -> None:
        """Push live/optimistic Aibox playback updates into Home Assistant immediately."""
        if not isinstance(playback, dict) or not playback:
            return

        current = self.data if isinstance(self.data, PhicommR1Status) else PhicommR1Status()
        next_raw = dict(current.raw or {})
        next_playback = dict(playback)
        resolved_playback_state = current.playback_state

        aibox_playing = self.client._aibox_lay_goi_y_dang_phat(next_playback)
        if aibox_playing is True:
            resolved_playback_state = "playing"
        elif aibox_playing is False:
            normalized_state = str(
                next_playback.get("state", next_playback.get("play_state", ""))
            ).strip().lower()
            resolved_playback_state = "idle" if normalized_state in {"idle", "stopped", "stop"} else "paused"

        if resolved_playback_state is not None:
            next_raw["playback_state"] = resolved_playback_state

        self.async_set_updated_data(
            replace(
                current,
                playback_state=resolved_playback_state,
                raw=next_raw,
                aibox_playback=next_playback,
            )
        )

    async def _async_update_data(self) -> PhicommR1Status:
        """Fetch state from device."""
        try:
            snapshot = await self.client.async_get_status_snapshot()
        except PhicommR1ApiError as err:
            raise UpdateFailed(str(err)) from err

        model = snapshot.get("model")
        playback_state = snapshot.get("playback_state")
        if not self._use_media_dispatch and self.client.protocol != PROTOCOL_WS_NATIVE:
            playback_state = None

        status = PhicommR1Status(
            model=model or None,
            playback_state=playback_state,
            raw=dict(snapshot.get("raw") or {}),
        )
        status.raw["model"] = model
        status.raw["playback_state"] = playback_state
        status.volume_current = snapshot.get("volume_current")
        status.volume_min = snapshot.get("volume_min")
        status.volume_max = snapshot.get("volume_max")

        # Poll audio system state (non-critical)
        with suppress(PhicommR1ApiError, Exception):
            audio_resp = await self.client.async_get_eq_config()
            if audio_resp:
                status.audio_state = audio_resp
                if "music_light_mode" in audio_resp and "music_light_mode" not in status.raw:
                    status.raw["music_light_mode"] = audio_resp.get("music_light_mode")

        # Poll AiboxPlus playback state (non-critical: suppress errors)
        with suppress(PhicommR1ApiError, Exception):
            aibox_pb = await self.client.async_aibox_get_playback_state()
            if aibox_pb:
                status.aibox_playback = aibox_pb
                # Override playback_state from aibox if it has a valid signal
                aibox_playing = self.client._aibox_lay_goi_y_dang_phat(aibox_pb)
                if aibox_playing is True:
                    status.playback_state = "playing"
                    status.raw["playback_state"] = "playing"
                elif aibox_playing is False:
                    if status.playback_state != "playing":
                        status.playback_state = "paused"
                        status.raw["playback_state"] = "paused"

        # Poll wake word state (non-critical)
        with suppress(PhicommR1ApiError, Exception):
            wake_resp = await self.client.async_wake_word_get_enabled()
            if wake_resp and ("enabled" in wake_resp or "enable" in wake_resp or "state" in wake_resp):
                enabled_val = wake_resp.get("enabled", wake_resp.get("enable", wake_resp.get("state")))
                parsed = self.client._aibox_phan_tich_bool(enabled_val)
                if parsed is not None:
                    status.wake_word["enabled"] = parsed
            sens_resp = await self.client.async_wake_word_get_sensitivity()
            if sens_resp and ("sensitivity" in sens_resp or "value" in sens_resp):
                status.wake_word["sensitivity"] = float(
                    sens_resp.get("sensitivity", sens_resp.get("value", 0.9))
                )

        # Poll custom AI state (non-critical)
        with suppress(PhicommR1ApiError, Exception):
            ai_resp = await self.client.async_custom_ai_get_enabled()
            if ai_resp and ("enabled" in ai_resp or "enable" in ai_resp or "state" in ai_resp):
                enabled_val = ai_resp.get("enabled", ai_resp.get("enable", ai_resp.get("state")))
                parsed = self.client._aibox_phan_tich_bool(enabled_val)
                if parsed is not None:
                    status.custom_ai["enabled"] = parsed

        # Poll chat wake-up state (non-critical)
        with suppress(PhicommR1ApiError, Exception):
            chat_resp = await self.client.async_chat_get_state()
            if chat_resp:
                state_value = chat_resp.get(
                    "state",
                    chat_resp.get("chat_state", chat_resp.get("status")),
                )
                if state_value is None:
                    if any(
                        key in chat_resp
                        for key in ("button_text", "buttonText", "button_enabled", "buttonEnabled")
                    ):
                        state_value = "ready"
                    elif "success" in chat_resp:
                        parsed_success = self.client._aibox_phan_tich_bool(chat_resp.get("success"))
                        if parsed_success is not None:
                            state_value = "ready" if parsed_success else "unavailable"

                if state_value is not None:
                    state_text = str(state_value).strip()
                    if state_text:
                        status.chat_state["state"] = state_text

                if "button_text" in chat_resp or "buttonText" in chat_resp or "text" in chat_resp:
                    button_text = chat_resp.get(
                        "button_text",
                        chat_resp.get("buttonText", chat_resp.get("text")),
                    )
                    status.chat_state["button_text"] = "" if button_text is None else str(button_text)

                parsed_enabled = None
                if (
                    "button_enabled" in chat_resp
                    or "buttonEnabled" in chat_resp
                    or "enabled" in chat_resp
                ):
                    parsed_enabled = self.client._aibox_phan_tich_bool(
                        chat_resp.get(
                            "button_enabled",
                            chat_resp.get("buttonEnabled", chat_resp.get("enabled")),
                        )
                    )
                    if parsed_enabled is not None:
                        status.chat_state["button_enabled"] = parsed_enabled

                if parsed_enabled is None:
                    inferred_enabled = _suy_ra_chat_button_enabled(status.chat_state.get("state"))
                    if inferred_enabled is not None:
                        status.chat_state["button_enabled"] = inferred_enabled

                resp_type = chat_resp.get("type")
                if resp_type is not None:
                    status.chat_state["last_response_type"] = str(resp_type)

        # Poll LED state (non-critical)
        with suppress(PhicommR1ApiError, Exception):
            led_resp = await self.client.async_led_get_state()
            if led_resp:
                status.led_state = led_resp

        latest_aibox_playback = self.client.get_last_aibox_playback()
        current_updated_at = int(status.aibox_playback.get("updated_at_ms") or 0) if status.aibox_playback else 0
        latest_updated_at = int(latest_aibox_playback.get("updated_at_ms") or 0) if latest_aibox_playback else 0
        if latest_updated_at > current_updated_at:
            status.aibox_playback = latest_aibox_playback
            latest_playing = self.client._aibox_lay_goi_y_dang_phat(latest_aibox_playback)
            if latest_playing is True:
                status.playback_state = "playing"
                status.raw["playback_state"] = "playing"
            elif latest_playing is False and status.playback_state != "playing":
                latest_state = str(
                    latest_aibox_playback.get("state", latest_aibox_playback.get("play_state", ""))
                ).strip().lower()
                resolved_state = "idle" if latest_state in {"idle", "stopped", "stop"} else "paused"
                status.playback_state = resolved_state
                status.raw["playback_state"] = resolved_state

        return status
