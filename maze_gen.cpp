#include <bits/stdc++.h>
using namespace std;

int main(int argc, char* argv[]) {
    // Mặc định mê cung cỡ 31x31 nếu Python không truyền tham số
    int width = 31;
    int height = 31;

    if (argc >= 3) {
        width = atoi(argv[1]);
        height = atoi(argv[2]);
    }

    // Tỉ lệ tạo vòng (0-100), có thể truyền thêm khi muốn chỉnh độ rối
    int braidPercent = 10;       // % ngõ cụt được phá để tạo lối vòng
    int extraLoopPercent = 1;    // % tường hành lang được mở ngẫu nhiên
    if (argc >= 4) braidPercent = atoi(argv[3]);
    if (argc >= 5) extraLoopPercent = atoi(argv[4]);

    // Kích thước phải >= 5 và là số lẻ, nếu không mê cung sẽ bị lỗi
    if (width < 5 || height < 5 || width % 2 == 0 || height % 2 == 0) {
        cerr << "Kich thuoc phai >= 5 va la so le!\n";
        return 1;
    }

    // Seed ngẫu nhiên thật sự (không lặp lại nếu chạy nhiều lần trong cùng 1 giây)
    mt19937 rng(random_device{}() ^
                (unsigned)chrono::steady_clock::now().time_since_epoch().count());

    // Khởi tạo toàn tường (1), sau đó đục lỗ bằng DFS
    vector<vector<int>> maze(height, vector<int>(width, 1));

    // Recursive backtracker (DFS lặp) -> mê cung cơ sở: mọi ô thông nhau,
    // ban đầu chỉ có duy nhất một đường đi (phần dưới sẽ thêm vòng).
    vector<pair<int, int>> stack;
    maze[1][1] = 0;
    stack.push_back({1, 1});

    const int dy[4] = {-2, 2, 0, 0};
    const int dx[4] = {0, 0, -2, 2};

    // Bước 1 ô (dùng khi phá tường hành lang để tạo vòng)
    const int sy[4] = {-1, 1, 0, 0};
    const int sx[4] = {0, 0, -1, 1};

    while (!stack.empty()) {
        int y = stack.back().first;
        int x = stack.back().second;

        // Xáo trộn thứ tự 4 hướng để mê cung không bị lặp lại
        int dirs[4] = {0, 1, 2, 3};
        shuffle(dirs, dirs + 4, rng);

        bool moved = false;
        for (int d = 0; d < 4; ++d) {
            int ny = y + dy[dirs[d]];
            int nx = x + dx[dirs[d]];

            // Chỉ đi trong vùng bên trong tường bao
            if (ny > 0 && ny < height - 1 && nx > 0 && nx < width - 1 && maze[ny][nx] == 1) {
                // Đục ô giữa và ô đích
                maze[(y + ny) / 2][(x + nx) / 2] = 0;
                maze[ny][nx] = 0;
                stack.push_back({ny, nx});
                moved = true;
                break;
            }
        }

        // Ngõ cụt -> quay lui
        if (!moved) {
            stack.pop_back();
        }
    }

    // ------------------------------------------------------------------
    // Thêm vòng lặp (loop) để có NHIỀU đường đi thay vì chỉ 1 đường duy nhất
    // ------------------------------------------------------------------
    auto randPercent = [&]() { return (int)(rng() % 100); };

    // (a) Phá một phần ngõ cụt: nối phòng cụt sang phòng bên cạnh -> tạo lối vòng
    for (int i = 1; i < height - 1; i += 2) {
        for (int j = 1; j < width - 1; j += 2) {
            int openCnt = 0;
            int cand[4], nc = 0;
            for (int d = 0; d < 4; ++d) {
                int cy = i + sy[d], cx = j + sx[d];
                if (cy < 1 || cy > height - 2 || cx < 1 || cx > width - 2) continue;
                if (maze[cy][cx] == 0) {
                    ++openCnt;               // lối đã mở
                } else {
                    cand[nc++] = d;          // tường có thể phá
                }
            }
            // Ngõ cụt (chỉ có 1 lối mở) -> thỉnh thoảng phá thêm 1 tường
            if (openCnt == 1 && nc > 0 && randPercent() < braidPercent) {
                int d = cand[rng() % nc];
                maze[i + sy[d]][j + sx[d]] = 0;
            }
        }
    }

    // (b) Mở thêm vài bức tường hành lang ngẫu nhiên -> nhiều lối tắt/đường vòng
    for (int i = 1; i < height - 1; ++i) {
        for (int j = 1; j < width - 1; ++j) {
            // Ô hành lang: một tọa độ lẻ, một tọa độ chẵn
            if (maze[i][j] == 1 && (i % 2) != (j % 2)) {
                if (randPercent() < extraLoopPercent) {
                    maze[i][j] = 0;
                }
            }
        }
    }

    // Đảm bảo điểm bắt đầu và điểm kết thúc luôn là đường đi
    maze[1][1] = 0;
    maze[height - 2][width - 2] = 0;

    // In ma trận ra màn hình để Python đọc
    for (int i = 0; i < height; ++i) {
        for (int j = 0; j < width; ++j) {
            cout << maze[i][j] << (j == width - 1 ? "" : " ");
        }
        cout << "\n";
    }

    return 0;
}
