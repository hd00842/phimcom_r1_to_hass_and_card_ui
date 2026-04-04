# Phicomm R1 cho Home Assistant

## 1. Cài đặt qua HACS
[![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=hd00842&repository=phimcom_r1_to_hass_and_card_ui&category=integration)

1. Bấm nút `Add to HACS` ở trên.
2. Thêm repository vào HACS.
3. Cài `Phicomm R1`.
4. Restart Home Assistant.

## 2. Cấu hình integration

Vào **Settings -> Devices & Services -> Add Integration** rồi tìm **Phicomm R1**.

Thiết lập khuyến nghị:

- `Tên`: `Phicomm R1`
- `Host`: IP của loa
- `Cổng`: `8080`
- `Cổng WS media (YouTube/Zing)`: `8082`
- `Chu kỳ cập nhật`: `15`
- `Dùng /media-dispatch để điều khiển phát`: bật
- `Chế độ giao thức`: `auto`

Gợi ý chọn giao thức:

- `auto`: nên dùng cho lần cài đầu tiên
- `ws_native`: dùng khi muốn ưu tiên kết nối native
- `http_bridge`: chỉ dùng nếu bạn biết chắc mình đang dùng bridge cũ
## 3. Coppy www/phicomm_r1
**Download file phicomm-r1-card.js và coppy vào www/phicomm_r1**
Sau đó vào **Settings ->Dashboards->Resources->Add resource
- Url nhập: /local/phicomm_r1/phicomm-r1-card.js
- Resource type -> JavaScript module -> Save
## 4 Tạo card trên lovelace
Sử dụng code sau:
```yaml
    type: custom:phicomm-r1-card
    entity: media_player.phimcomm_r1
    title: Phicomm R1

Có thể sử dụng thêm option max_height: 90vh hoặc max_height: 500px để giới hạn chiều cao của card ví dụ
```yaml
    type: custom:phicomm-r1-card
    entity: media_player.phimcomm_r1
    title: Phicomm R1
    max_height: 500px