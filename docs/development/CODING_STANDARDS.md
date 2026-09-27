---
title: 编码规范
version: 1.0.0
status: Published
last_updated: 2026-09-26
owner: Tech Lead
reviewers: [资深工程师, 架构师, QA Lead]
approvers: [Tech Lead]
classification: Internal
doc_id: DOC-DEV-001
tags: [开发, 编码规范, Python, TypeScript, React, 最佳实践, 工程规范]
related_docs: [DOC-DEV-004, DOC-DEV-005, DOC-QA-004]
changelog: |
  v1.0.0 (2026-09-26): 初版创建 - Tech Lead
---

# 编码规范

## 1. 通用原则

### 1.1 核心哲学
- **可读性优先**: 代码写给人看，附带能在机器上运行
- **显式优于隐式**: 清晰表达意图，避免魔法数字/字符串/行为
- **单一职责**: 函数/类/模块只做一件事，做好一件事
- **防御性编程**: 输入验证、边界检查、优雅降级、快速失败
- **最小惊讶原则**: API 行为符合直觉，避免副作用

### 1.2 代码风格统一
- **强制工具化**: 所有风格规则由 Linter/Formatter 强制执行，不依赖人工 Review
- **CI 门禁**: 代码推送必须通过 `lint`、`format`、`type-check`、`test` 才能合并
- **IDE 集成**: 统一 `.vscode/settings.json`、`.editorconfig`、保存时自动格式化

---

## 2. Python (Backend) 规范

### 2.1 环境与工具链
| 工具 | 版本 | 用途 | 配置文件 |
|------|------|------|----------|
| Python | 3.11+ | 运行时 | `.python-version` / `pyproject.toml` |
| Ruff | 最新 | Lint + Format (替代 Black/Flake8/isort) | `pyproject.toml` |
| MyPy | 1.8+ | 静态类型检查 (strict 模式) | `pyproject.toml` |
| PyTest | 8.0+ | 单元/集成测试 | `pyproject.toml` |
| PyProject | - | 统一构建配置 | `pyproject.toml` |

### 2.2 代码风格
```toml
# pyproject.toml 关键配置
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "DTZ", "T10", "ARG", "PTH", "ERA", "PD", "PGH", "PL", "TRY", "NPY", "RSE", "RET", "SIM", "TCH", "INT", "LOG"]
ignore = ["E501"]  # 行长由 formatter 处理
per-file-ignores = ["tests/*: S101"]  # 测试中允许 assert

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
no_implicit_optional = true
```

### 2.3 命名规范
| 类型 | 规范 | 示例 |
|------|------|------|
| 模块/包 | 小写下划线 | `order_service.py`, `user_management` |
| 类 | PascalCase | `OrderService`, `UserRepository` |
| 函数/方法/变量 | snake_case | `get_user_by_id`, `order_total` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_PAGE_SIZE` |
| 私有成员 | `_single_leading_underscore` | `_internal_cache` |
| 类型变量 | `TypeVar` PascalCase | `T`, `UserT`, `ResponseT` |
| 泛型参数 | 单大写字母或描述性 | `T`, `K`, `V`, `RequestT`, `ResponseT` |

### 2.4 类型注解 (强制)
```python
# 所有公共函数必须有完整类型注解
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class OrderQueryParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    status: Optional[OrderStatus] = None
    shop_id: int

async def get_orders(
    params: OrderQueryParams,
    db: AsyncSession,
    current_user: CurrentUser,
) -> PaginatedResponse[OrderDTO]:
    """获取订单列表 (分页、筛选、权限校验)"""
    # 实现...
    pass
```

### 2.5 文档字符串
```python
def calculate_commission(
    order_amount: Decimal,
    rate: Decimal,
    *,
    min_commission: Decimal = Decimal("0"),
    max_commission: Optional[Decimal] = None,
) -> Decimal:
    """
    计算订单佣金。

    Args:
        order_amount: 订单金额 (元)，必须 >= 0
        rate: 佣金比率，范围 [0, 1]
        min_commission: 最低佣金，默认 0
        max_commission: 最高佣金上限，默认无上限

    Returns:
        计算后的佣金金额 (元)，已应用上下限

    Raises:
        ValueError: 参数校验失败
        CommissionCalculationError: 计算溢出或异常

    Example:
        >>> calculate_commission(Decimal("100.00"), Decimal("0.05"))
        Decimal('5.00')
    """
    if order_amount < 0:
        raise ValueError("order_amount must be non-negative")
    # ...
```

### 2.6 错误处理
```python
# 自定义异常层级
class AppException(Exception):
    """业务异常基类"""
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)

class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(f"{resource} not found: {identifier}", "NOT_FOUND", 404)

class ValidationError(AppException):
    def __init__(self, field: str, message: str):
        super().__init__(f"Validation failed for {field}: {message}", "VALIDATION_ERROR", 422)

# 统一异常处理器 (FastAPI 示例)
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )
```

### 2.7 数据库操作
```python
# 使用 SQLAlchemy 2.0+ Async ORM
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

async def get_order_with_items(
    db: AsyncSession,
    order_id: int,
    user_id: int,
) -> Optional[Order]:
    """获取订单及关联项 (权限校验、预加载防 N+1)"""
    stmt = (
        select(Order)
        .where(Order.id == order_id, Order.user_id == user_id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# 批量操作示例
async def bulk_update_order_status(
    db: AsyncSession,
    order_ids: List[int],
    new_status: OrderStatus,
    operator_id: int,
) -> int:
    """批量更新订单状态 (乐观锁、审计日志)"""
    async with db.begin():
        # 乐观锁版本号校验
        stmt = (
            update(Order)
            .where(Order.id.in_(order_ids), Order.version == OrderVersion.current())
            .values(status=new_status, version=Order.version + 1, updated_by=operator_id)
            .execution_options(synchronize_session="fetch")
        )
        result = await db.execute(stmt)
        # 记录审计日志...
        return result.rowcount
```

### 2.8 异步编程
```python
# 正确使用 async/await，避免阻塞
import asyncio
from contextlib import asynccontextmanager

class ExternalAPIClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)
        self._semaphore = asyncio.Semaphore(20)  # 限制并发

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._client.aclose()

    async def get(self, path: str, params: dict) -> dict:
        async with self._semaphore:
            response = await self._client.get(path, params=params)
            response.raise_for_status()
            return response.json()

# 并发控制示例
async def fetch_multiple_orders(order_ids: List[int]) -> List[Order]:
    semaphore = asyncio.Semaphore(10)
    async def fetch_one(oid: int) -> Order:
        async with semaphore:
            return await get_order(oid)
    return await asyncio.gather(*[fetch_one(oid) for oid in order_ids])
```

### 2.9 测试规范
```python
# pytest 规范
# tests/unit/test_order_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

class TestOrderService:
    @pytest.fixture
    def mock_db(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def service(self, mock_db):
        return OrderService(db=mock_db)

    @pytest.mark.parametrize("amount,rate,expected", [
        (Decimal("100.00"), Decimal("0.05"), Decimal("5.00")),
        (Decimal("0"), Decimal("0.1"), Decimal("0")),
        (Decimal("1000"), Decimal("0"), Decimal("0")),
    ])
    async def test_calculate_commission(self, service, amount, rate, expected):
        result = await service.calculate_commission(amount, rate)
        assert result == expected

    async def test_create_order_insufficient_stock(self, service, mock_db):
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        with pytest.raises(InsufficientStockError):
            await service.create_order(product_id=1, quantity=100)
```

---

## 3. TypeScript/React (Frontend) 规范

### 3.1 环境与工具链
| 工具 | 版本 | 用途 | 配置文件 |
|------|------|------|----------|
| TypeScript | 5.4+ | 类型检查 | `tsconfig.json` |
| ESLint | 8.57+ | Lint | `eslint.config.js` (Flat Config) |
| Prettier | 3.2+ | 格式化 | `.prettierrc` |
| Stylelint | 16.3+ | CSS/SCSS Lint | `.stylelintrc.json` |
| Vitest | 1.4+ | 单元测试 | `vitest.config.ts` |
| React Testing Library | 14.2+ | 组件测试 | - |

### 3.2 tsconfig.json 关键配置
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@hooks/*": ["src/hooks/*"],
      "@utils/*": ["src/utils/*"],
      "@api/*": ["src/api/*"],
      "@types/*": ["src/types/*"]
    }
  },
  "include": ["src/**/*", "vite.config.ts"],
  "exclude": ["node_modules", "dist", "**/*.stories.tsx"]
}
```

### 3.2 命名规范
| 类型 | 规范 | 示例 |
|------|------|------|
| 文件/目录 | kebab-case | `order-list.tsx`, `use-order-hooks.ts` |
| 组件 | PascalCase | `OrderList.tsx`, `OrderCard.tsx` |
| Hook | camelCase + `use` 前缀 | `useOrderList`, `useDebounce` |
| 函数/变量/Props | camelCase | `fetchOrders`, `orderList`, `onOrderClick` |
| 类型/接口 | PascalCase + `I`/`Props` 后缀 | `IOrder`, `OrderListProps`, `ApiResponse<T>` |
| 枚举/常量 | PascalCase / UPPER_SNAKE_CASE | `OrderStatus`, `DEFAULT_PAGE_SIZE` |
| CSS 类名 | kebab-case (BEM) | `.order-list__item--active` |

### 3.3 组件设计规范
```tsx
// 组件文件结构标准
// components/order/OrderCard.tsx

import React, { memo, useCallback } from 'react';
import { OrderStatus } from '@/types/order';
import { formatCurrency } from '@/utils/currency';
import { StatusBadge } from '@/components/ui/StatusBadge';
import styles from './OrderCard.module.css';

export interface OrderCardProps {
  /** 订单数据 */
  order: IOrder;
  /** 点击回调 */
  onClick?: (orderId: number) => void;
  /** 是否显示操作按钮 */
  showActions?: boolean;
}

export const OrderCard = memo(function OrderCard({
  order,
  onClick,
  showActions = false,
}: OrderCardProps) {
  const handleClick = useCallback(() => {
    onClick?.(order.id);
  }, [onClick, order.id]);

  return (
    <article className={styles.card} onClick={handleClick} tabIndex={0} role="button">
      <header className={styles.header}>
        <h3 className={styles.orderId}>订单 #{order.id}</h3>
        <StatusBadge status={order.status} />
      </header>
      <div className={styles.body}>
        <p className={styles.amount}>
          {formatCurrency(order.totalAmount)}
        </p>
        <p className={styles.time}>{formatRelativeTime(order.createdAt)}</p>
      </div>
      {showActions && (
        <footer className={styles.actions}>
          <button className={styles.btn} onClick={(e) => { e.stopPropagation(); viewDetail(order.id); }}>
            查看详情
          </button>
        </footer>
      )}
    </article>
  );
});

OrderCard.displayName = 'OrderCard';
```

### 3.4 Hooks 规范
```tsx
// hooks/useOrderList.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { orderApi } from '@/api/order';
import { IOrder, OrderQueryParams } from '@/types/order';

export function useOrderList(params: OrderQueryParams) {
  return useQuery({
    queryKey: ['orders', params],
    queryFn: () => orderApi.list(params),
    staleTime: 30_000, // 30 秒内不重复请求
    placeholderData: (prev) => prev, // 保持旧数据避免闪烁
  });
}

export function useUpdateOrderStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: OrderStatus }) =>
      orderApi.updateStatus(id, status),
    onMutate: async (variables) => {
      // 乐观更新
      await queryClient.cancelQueries({ queryKey: ['orders'] });
      const previous = queryClient.getQueryData(['orders']);
      queryClient.setQueryData(['orders'], (old) => updateOrderStatus(old, variables));
      return { previous };
    },
    onError: (err, variables, context) => {
      queryClient.setQueryData(['orders'], context?.previous);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
}
```

### 3.5 状态管理
```tsx
// store/orderStore.ts (Zustand 示例)
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { IOrder, OrderStatus } from '@/types/order';

interface OrderState {
  selectedOrderId: number | null;
  filters: OrderQueryParams;
  setSelectedOrder: (id: number | null) => void;
  setFilters: (filters: Partial<OrderQueryParams>) => void;
  clearFilters: () => void;
}

const defaultFilters: OrderQueryParams = {
  page: 1,
  size: 20,
  status: undefined,
  shopId: undefined,
};

export const useOrderStore = create<OrderState>()(
  immer((set) => ({
    selectedOrderId: null,
    filters: defaultFilters,
    setSelectedOrder: (id) => set((state) => { state.selectedOrderId = id; }),
    setFilters: (newFilters) => set((state) => { Object.assign(state.filters, newFilters); }),
    clearFilters: () => set((state) => { state.filters = defaultFilters; }),
  }))
);
```

### 3.6 样式规范
```css
/* components/order/OrderCard.module.css */
.card {
  display: flex;
  flex-direction: column;
  padding: var(--spacing-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: box-shadow var(--duration-fast) ease;
  cursor: pointer;

  &:hover {
    box-shadow: var(--shadow-md);
  }

  &:focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.orderId {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text);
}

.body {
  flex: 1;
  margin-bottom: var(--spacing-md);
}

.amount {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 var(--spacing-xs);
}

.time {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin: 0;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--color-border);
}

.btn {
  padding: var(--spacing-xs) var(--spacing-md);
  font-size: var(--font-size-sm);
  border-radius: var(--radius-sm);
  border: none;
  background: var(--color-primary);
  color: white;
  cursor: pointer;
  transition: background var(--duration-fast);

  &:hover {
    background: var(--color-primary-hover);
  }

  &:focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
}
```

### 3.7 无障碍 (a11y)
```tsx
// 所有交互元素必须满足：
// - 语义化 HTML (button, nav, main, article, header, footer)
// - 键盘可达 (tabIndex, onKeyDown 支持 Enter/Space)
// - 焦点可见 (focus-visible 样式)
// - ARIA 属性 (aria-label, aria-expanded, aria-controls, role)
// - 颜色对比度 ≥ 4.5:1 (WCAG AA)
// - 图片有 alt 属性 (装饰性图片 alt="")

<button
  aria-label="删除订单 #123"
  aria-pressed={false}
  onClick={handleDelete}
  className={styles.deleteBtn}
>
  <IconTrash aria-hidden="true" />
</button>
```

---

## 4. API 接口规范

### 4.1 RESTful 设计原则
| 资源 | GET (列表) | GET (单个) | POST (创建) | PUT/PATCH (更新) | DELETE (删除) |
|------|------------|------------|-------------|------------------|---------------|
| `/orders` | 查询列表 (分页/筛选) | - | 创建订单 | - | - |
| `/orders/{id}` | - | 查询详情 | - | 更新订单 | 删除订单 |
| `/orders/{id}/items` | 查询明细 | - | 添加明细 | - | - |

### 4.2 统一响应格式
```typescript
// 成功响应
interface ApiResponse<T> {
  code: 200;
  message: 'success';
  data: T;
  meta?: {
    page?: number;
    size?: number;
    total?: number;
  };
}

// 错误响应
interface ApiError {
  code: number;        // 业务错误码
  message: string;     // 用户可读错误信息
  details?: Record<string, string[]>; // 字段级错误详情
  traceId: string;     // 链路追踪 ID
}

// 标准错误码
enum ErrorCode {
  SUCCESS = 200,
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401,
  FORBIDDEN = 403,
  NOT_FOUND = 404,
  VALIDATION_ERROR = 422,
  CONFLICT = 409,
  TOO_MANY_REQUESTS = 429,
  INTERNAL_ERROR = 500,
  SERVICE_UNAVAILABLE = 503,
}
```

### 4.3 版本控制
```http
# URL 版本控制 (推荐)
GET /api/v1/orders
GET /api/v2/orders

# Header 版本控制 (备选)
Accept: application/vnd.douyin.v1+json
```

---

## 5. Git 提交规范

### 5.1 Commit Message 格式 (Conventional Commits)
```
<type>(<scope>): <subject>

<body>

<footer>
```

| type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(order): add bulk export API` |
| `fix` | Bug 修复 | `fix(order): handle null status in export` |
| `refactor` | 重构 (非功能/非修复) | `refactor(order): extract export logic to service` |
| `perf` | 性能优化 | `perf(order): add index for status query` |
| `style` | 代码风格 (格式化、分号等) | `style: format order service with ruff` |
| `docs` | 文档更新 | `docs(order): update export API doc` |
| `test` | 测试相关 | `test(order): add export edge case tests` |
| `chore` | 构建/工具/依赖/配置 | `chore: upgrade ruff to 0.4.0` |
| `revert` | 回滚 | `revert: feat(order): add bulk export API` |

### 5.2 Scope 规范
| scope | 说明 |
|-------|------|
| `order` | 订单模块 |
| `product` | 商品模块 |
| `auth` | 认证授权 |
| `api` | 通用 API 基础设施 |
| `ui` | 前端 UI 组件 |
| `infra` | 基础设施/配置/部署 |
| `deps` | 依赖升级 |
| `release` | 发布相关 |

### 5.3 Body 和 Footer
```
# Body: 详细说明变更动机、设计决策、破坏性变更
# 可选，但破坏性变更必须写明

# Footer: 关联 Issue、Breaking Change 声明、Co-authored-by
Closes #123
Breaking Change: API response structure changed, see migration guide
Co-authored-by: Zhang San <zhangsan@example.com>
```

---

## 5. 代码审查标准
详见 `CODE_REVIEW_CHECKLIST.md`

---

## 6. 附录：常用配置文件模板

### 6.1 .editorconfig
```ini
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.{md,mdx,yml,yaml,json}]
indent_size = 2

[*.{py}]
indent_size = 4

[*.{ts,tsx,js,jsx,css,scss}]
indent_size = 2
```

### 6.2 .prettierrc
```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "bracketSpacing": true,
  "arrowParens": "avoid",
  "endOfLine": "lf"
}
```

### 6.3 .gitignore 通用模板
```gitignore
# Dependencies
node_modules/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Build outputs
dist/
build/
*.egg-info/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/*
!.vscode/settings.json
!.vscode/extensions.json
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Test coverage
coverage/
.htmlcov/

# Misc
*.tmp
*.temp
*.swp
*.swo
```

---

## 7. 违规处理与例外

| 违规类型 | 处理方式 |
|----------|----------|
| Lint/Format 不通过 | CI 自动拦截，不可合并 |
| 类型检查不通过 (MyPy/TS strict) | CI 自动拦截，不可合并 |
| 测试覆盖率低于阈值 | CI 警告，核心模块必须达标 |
| 命名/注释规范违规 | Review 时指出，修复后合并 |
| 架构/设计原则违背 | Reviewer 判定 Request Changes，需重构 |
| 紧急热修复例外 | 事后 24h 内补全规范、补测、补文档 |

---

*文档版本: v1.0.0 | 维护者: Tech Lead | 更新周期: 季度或重大技术栈升级时*
EOF