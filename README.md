# Phicomm R1 cho Home Assistant

README này chỉ giữ lại phần **cài đặt** và **cấu hình**.

[![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=hd00842&repository=phimcom_r1_to_hass_and_card_ui&category=integration)

## 1. Chuẩn bị

- Home Assistant đã chạy bình thường
- Phicomm R1 cùng mạng LAN với Home Assistant
- Biết địa chỉ IP của loa, ví dụ: `192.168.1.50`

## 2. Cài nhanh qua HACS

1. Bấm nút `Add to HACS` ở trên.
2. Thêm repository vào HACS.
3. Cài `Phicomm R1`.
4. Restart Home Assistant.

Nếu bạn dùng custom card, vẫn làm thêm phần `Cài đặt custom card` bên dưới.

## 3. Cài đặt integration thủ công

Sao chép thư mục sau vào Home Assistant:

```text
config/
  custom_components/
    phicomm_r1/
```

Sau đó:

1. Restart Home Assistant.
2. Vào **Settings -> Devices & Services -> Add Integration**.
3. Tìm **Phicomm R1**.
4. Nhập thông tin cấu hình.

## 4. Cấu hình integration

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
- `http_bridge`: chỉ dùng nếu hệ thống của bạn đang chạy bridge cũ

Lưu ý về cổng:

- `8080`: dùng cho `ws_native` hoặc `auto`
- `2847`: chỉ dùng khi bạn biết chắc mình đang dùng `http_bridge`

## 5. Cài đặt custom card

Sao chép file sau vào Home Assistant:

```text
config/
  www/
    phicomm_r1/
      phicomm-r1-card.js
```

## 6. Khai báo resource cho card

Vào **Settings -> Dashboards -> Resources** và thêm:

- `URL`: `/local/phicomm_r1/phicomm-r1-card.js`
- `Type`: `JavaScript Module`

## 7. Thêm card vào dashboard

```yaml
type: custom:phicomm-r1-card
entity: media_player.phicomm_r1
title: Phicomm R1
```

Nếu entity của bạn không phải `media_player.phicomm_r1`, hãy thay bằng entity thực tế trong Home Assistant.

## 8. Sau khi cài xong

Nếu card chưa hiển thị đúng:

1. Hard refresh trình duyệt.
2. Nếu vẫn chưa cập nhật, restart lại Home Assistant.
