# Hướng dẫn cài đặt, chạy và kiểm thử

Tài liệu này áp dụng cho trạng thái hiện tại của project: **PHASE 1** gồm cấu hình,
tải mạng đường OpenStreetMap, chuẩn hóa thuộc tính và cache graph. Các lệnh UI, AI và
routing chưa được liệt kê vì các phase tương ứng chưa được triển khai.

## 1. Yêu cầu hệ thống

- Python 3.11–3.14.
- Kết nối Internet cho lần tải graph OSM đầu tiên.
- Khoảng 1 GB dung lượng trống để cài môi trường GIS và lưu graph/cache.
- Chạy lệnh tại thư mục gốc project, tức thư mục chứa `pyproject.toml`.

Kiểm tra Python:

```powershell
python --version
```

## 2. Cài đặt trên Windows bằng PowerShell

Tạo virtual environment:

```powershell
python -m venv .venv
```

Kích hoạt môi trường:

```powershell
.\.venv\Scripts\Activate.ps1
```

Nếu PowerShell không cho chạy script kích hoạt, không cần thay đổi execution policy.
Có thể gọi Python trong môi trường trực tiếp như sau:

```powershell
.\.venv\Scripts\python.exe --version
```

Cài core dependency và công cụ kiểm thử cho Phase 1:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Nếu không kích hoạt virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Để cài thêm toàn bộ dependency đã dự kiến cho các phase AI/UI:

```powershell
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
```

## 3. Cài đặt trên macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## 4. Cấu hình

Tạo `.env` từ file mẫu.

PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Cấu hình mặc định quan trọng:

```dotenv
OSM_PLACE=Hanoi, Vietnam
OSM_VEHICLE_PROFILE=car
OSM_REQUEST_TIMEOUT_SECONDS=180
OSM_CACHE_DIR=data/graph
```

Giá trị hợp lệ của `OSM_VEHICLE_PROFILE` là `car` hoặc `motorbike`. Không đưa API key
thật vào Git; `.env` đã được ignore.

## 5. Chạy thử với graph nhỏ tại Hà Nội

Nên bắt đầu bằng quận Hoàn Kiếm để xác nhận môi trường GIS, Nominatim và Overpass hoạt
động trước khi tải toàn bộ Hà Nội:

```powershell
python scripts/download_map.py --place "Hoan Kiem District, Hanoi, Vietnam"
```

Kết quả mẫu đã được xác minh:

```text
Study area: Hoan Kiem District, Hanoi, Vietnam
Vehicle profile: car
Nodes: 461
Directed edges: 1,085
Total directed-edge length: 120.9 km
Weakly connected components: 1
```

Chạy lại cùng lệnh sẽ đọc file GraphML trong `data/graph` thay vì tải lại.

## 6. Tải graph Hà Nội

Sử dụng cấu hình trong `.env`:

```powershell
python scripts/download_map.py
```

Hoặc chỉ định trực tiếp:

```powershell
python scripts/download_map.py --place "Hanoi, Vietnam" --vehicle car
python scripts/download_map.py --place "Hanoi, Vietnam" --vehicle motorbike
```

Buộc tải lại và thay cache tương ứng:

```powershell
python scripts/download_map.py --force
```

Ranh giới hành chính toàn Hà Nội tạo truy vấn Overpass lớn và có thể mất nhiều phút hoặc
timeout. Khi phát triển, dùng một quận của Hà Nội là cách kiểm tra hợp lý. Graph motorbike
là best-effort theo OSM tags, không phải cam kết đầy đủ về hạn chế giao thông pháp lý.

## 7. Chạy kiểm thử

Unit tests:

```powershell
python -m pytest -q
```

Kiểm tra lint và format:

```powershell
python -m ruff check app scripts tests
python -m ruff format --check app scripts tests
```

Kiểm tra type hints:

```powershell
python -m mypy app scripts
```

Kiểm tra compile toàn bộ source:

```powershell
python -m compileall -q app scripts tests
```

Chạy toàn bộ quality gate trên PowerShell:

```powershell
python -m pytest -q
python -m ruff check app scripts tests
python -m ruff format --check app scripts tests
python -m mypy app scripts
python -m compileall -q app scripts tests
```

Nếu không kích hoạt virtual environment, thay `python` bằng
`.\.venv\Scripts\python.exe` trong các lệnh trên.

## 8. Dữ liệu được tạo ở đâu?

- Graph đã chuẩn hóa: `data/graph/*.graphml`.
- Metadata của graph: `data/graph/*.json`.
- HTTP cache nội bộ của OSMnx: `data/graph/http/`.

Các file này không được commit. Cache key phụ thuộc vào địa điểm, vehicle profile và các
tham số tạo graph, giúp tránh dùng nhầm graph giữa hai cấu hình.

## 9. Xử lý lỗi thường gặp

### `ModuleNotFoundError: No module named 'osmnx'`

Virtual environment chưa được kích hoạt hoặc dependency chưa được cài:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### Overpass timeout hoặc không tải được toàn Hà Nội

- Thử lại sau vì public Overpass có thể đang quá tải.
- Tăng `OSM_REQUEST_TIMEOUT_SECONDS` trong `.env`.
- Kiểm tra trước với quận Hoàn Kiếm.
- Không xóa cache GraphML đã tải thành công nếu muốn chạy offline.

### PowerShell chặn `Activate.ps1`

Dùng trực tiếp `.\.venv\Scripts\python.exe` như các ví dụ phía trên; không bắt buộc phải
activate môi trường.

### Kiểm tra đang dùng đúng Python

```powershell
python -c "import sys; print(sys.executable)"
python -c "import osmnx; print(osmnx.__version__)"
```

