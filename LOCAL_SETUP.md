# Local Portfolio Setup

This note records the exact setup used to verify the Knowledge Quality
dashboard on Windows.

## 1. Install dependencies

```powershell
python -m uv sync --python 3.10 --no-install-package llama-cpp-python --default-index https://pypi.tuna.tsinghua.edu.cn/simple
```

`llama-cpp-python` is skipped because it requires a native C/C++ toolchain on
Windows. The portfolio feature does not depend on local llama.cpp inference.

## 2. Start the app

```powershell
$env:GRADIO_SERVER_NAME='127.0.0.1'
$env:GRADIO_SERVER_PORT='7860'
$env:NO_PROXY='127.0.0.1,localhost'
$env:no_proxy='127.0.0.1,localhost'
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
python -m uv run --no-sync python app.py
```

Open: `http://127.0.0.1:7860`

The default local credentials are `admin` / `admin`.

## 3. Seed demo feedback

```powershell
python -m uv run --no-sync python examples/seed_knowledge_quality_demo.py --seed
```

Then open **Resources -> Knowledge Quality**.

Clean up the demo feedback:

```powershell
python -m uv run --no-sync python examples/seed_knowledge_quality_demo.py --cleanup
```

## 4. Run targeted tests

```powershell
python -m uv run --no-sync pytest libs/ktem/ktem_tests/test_knowledge_quality.py -q
```
