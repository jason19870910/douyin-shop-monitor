# 开发环境与运行说明

推荐在本地与 CI 中使用 Python 3.11（兼容性最好，能避免在 Windows 上构建 pydantic-core 时出现本机编译问题）。

快速上手（Windows / macOS / Linux）：

1. 安装 Python 3.11（建议从 https://www.python.org/downloads/ 下载安装程序）。
2. 在仓库根目录创建并激活虚拟环境：

   - Windows (PowerShell):

     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

   - macOS / Linux:

     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```

3. 安装依赖：

   ```bash
   python -m pip install --upgrade pip
   pip install -r src/backend/requirements-dev.txt
   ```

4. 运行测试：

   ```bash
   pytest -c pytest.ini
   ```

注意（Windows）：

- 如果你必须使用 Python >= 3.14，某些包（如 `pydantic-core`）可能需要在本机编译，这会要求安装 **Visual C++ Build Tools**（包含 Windows SDK）以及 **Rust toolchain**（`rustup`）。若不希望安装这些系统依赖，请使用 Python 3.11。 

- 在 CI 中我们推荐使用 Python 3.11 来避免额外的系统依赖安装步骤。

CI 建议：仓库已包含一个 GitHub Actions 工作流示例（`.github/workflows/ci.yml`），用于在 Python 3.11 下运行 lint 与测试。你可以根据团队需要调整。 

如需我为你生成其它 CI 平台或更严格的 lint 规则配置，告诉我即可。
