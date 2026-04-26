# ElderGo-KL

  This is a code bundle for ElderGo KL. The original project is available at https://www.figma.com/design/ZBhP0dT1Vp8p9a46BeErE1/ElderGo-KL.

  ## Running the code

  Run `npm i` to install the dependencies.

  Run `npm run dev` to start the development server.



```
backend/
│
├── app/
│   ├── main.py              # 入口
│   │
│   ├── api/                # 路由层（Controller）
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── users.py
│   │   │   │   ├── routes.py
│   │   │   │   └── health.py
│   │   │   └── router.py
│   │
│   ├── core/               # 核心配置
│   │   ├── config.py
│   │   ├── security.py
│   │
│   ├── models/             # 数据库模型（ORM）
│   │   ├── user.py
│   │   └── route.py
│   │
│   ├── schemas/            # Pydantic schemas（数据验证）
│   │   ├── user.py
│   │   └── route.py
│   │
│   ├── services/           # 业务逻辑（重点）
│   │   ├── user_service.py
│   │   └── route_service.py
│   │
│   ├── db/
│   │   ├── session.py      # DB连接
│   │   ├── base.py         # Base model
│   │
│   └── utils/              # 工具函数
│       └── helpers.py
│
├── tests/                  # 测试
│   └── test_users.py
│
├── requirements.txt
├── .env
└── alembic/ (optional)
```





````markdown id="readme-eldergo-kl"
# ElderGo KL 🚆👴

A senior-friendly public transport navigation system designed for the Klang Valley.  
ElderGo KL simplifies complex route options into safe, accessible, and easy-to-understand journeys for elderly users.

---

## 📌 Project Overview

In Kuala Lumpur and the Klang Valley, elderly users often struggle with existing transport apps due to:
- Information overload (too many route choices)
- Small text and poor readability
- Lack of accessibility information (lifts, walking distance, transfers)

**ElderGo KL solves this by focusing on simplicity and accessibility.**

---

## 🎯 Key Features

- 🧭 Simplified route recommendation (best route only)
- 👓 Large, readable UI (3-level font scaling)
- ♿ Accessibility-aware navigation (lifts, ramps, walking distance)
- 🏠 One-tap "Home" navigation button
- 🌐 Multi-language support (EN / BM)

---

## 🏗️ Project Structure

```bash
project-root/
│
├── frontend/        # React application
├── backend/         # Python backend
├── docs/            # Documentation
└── README.md
````

---

## ⚙️ Tech Stack

* Frontend: React
* Backend: Python
* Version Control: Git
* Repository: GitHub

---

## 👥 Team Members



---

## 🧪 Development Approach

This project uses **Pair Programming**:

* Driver: writes code
* Navigator: reviews and guides
* Roles switch regularly

---

## 🚀 Getting Started

### 1. Clone repository

```bash
git clone <your-repo-url>
```

### 2. Install dependencies

Frontend:

```bash
cd frontend
npm install
```

Backend:

```bash
cd backend
pip install -r requirements.txt
```

### 3. Run project

Frontend:

```bash
npm start
```

Backend:

```bash
python app.py
```

---

## 📄 Documentation

* Pair Programming Report
* System Design (A&D)
* User Personas

---

## 📌 Notes

This project is developed for academic purposes.

````

---

# ✅ Git guidelines（`CONTRIBUTING.md` or README）

```markdown id="git-guidelines"
# Git Workflow & Contribution Guidelines

## 🌿 Branch Strategy

We follow a simplified Git workflow:

- `main` → stable production-ready code  
- `dev` → integration branch  
- `feature/*` → new features  
- `fix/*` → bug fixes  

### Example:
````

feature/login-ui
feature/route-algorithm
fix/navigation-bug

```

---

## 🔄 Workflow

1. Create a new branch from `dev`
2. Implement feature using Pair Programming
3. Commit changes with proper message format
4. Push branch to GitHub
5. Create Pull Request → merge into `dev`

---

## 📝 Commit Message Convention

We follow a structured commit format:

```

<type>: <short description>

```

### Types:

- `feat` → new feature  
- `fix` → bug fix  
- `docs` → documentation  
- `style` → formatting (no logic change)  
- `refactor` → code restructuring  
- `test` → testing  
- `chore` → maintenance  

---

### ✅ Examples

```

feat: add simplified route recommendation
fix: correct navigation button alignment
docs: update README with setup instructions
refactor: improve route scoring logic

```

---

## 🚫 What to Avoid

- ❌ vague messages like: "update", "fix stuff"
- ❌ committing large unrelated changes together
- ❌ pushing directly to main branch

---

## 👥 Pair Programming Rules

- Roles must switch regularly
- Both members review every commit
- Code should not be committed without mutual agreement

---

## 🔍 Code Review

Before merging:
- Ensure code is readable
- Check for bugs
- Verify feature works as expected
```

---

