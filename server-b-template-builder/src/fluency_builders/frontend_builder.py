"""
Frontend AI Fluency Builder
Creates realistic React apps with controlled, subtle bugs.

Four archetypes — candidate gets one based on company domain:
  • task_board  — classic project mgmt app (productivity, PM tools)
  • dashboard   — analytics/KPI dashboard (SaaS, fintech, data)
  • form_wizard — multi-step form/onboarding (HR, recruiting, fintech)
  • api_feed    — data feed with filtering/pagination (marketplace, e-commerce, social)

Within each archetype, bugs are drawn from a pool; difficulty controls how many are
injected, so no two candidates at different companies see the exact same bug set.
"""

import json
import random
import logging
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)

# ── Domain → archetype mapping ────────────────────────────────────────────────

_DOMAIN_ARCHETYPE: List[Tuple[List[str], str]] = [
    (["analytics", "metrics", "dashboard", "bi ", "business intelligence", "saas",
      "finance", "fintech", "banking", "reporting", "data"], "dashboard"),
    (["onboard", "recruit", "hr ", "human resource", "signup", "registration",
      "checkout", "payment", "kyc", "wizard", "form"], "form_wizard"),
    (["marketplace", "ecommerce", "e-commerce", "shop", "store", "product",
      "catalogue", "catalog", "social", "feed", "news", "content", "media"], "api_feed"),
]


def pick_archetype(company_name: str = "", job_description: str = "", tech_stack: Optional[List[str]] = None) -> str:
    """Return the best-fit archetype for the given company/role context."""
    import re
    text = f"{company_name} {job_description}".lower()

    def _matches(keywords: List[str]) -> bool:
        for kw in keywords:
            kw = kw.strip()
            # Use word-boundary matching so "product" doesn't match "productivity"
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, text):
                return True
        return False

    for keywords, archetype in _DOMAIN_ARCHETYPE:
        if _matches(keywords):
            return archetype
    return "task_board"


# ── Shared boilerplate helpers ────────────────────────────────────────────────

def _base_pkg(name: str, deps: Dict[str, str] = None, dev_deps: Dict[str, str] = None) -> str:
    base_deps = {"react": "^18.2.0", "react-dom": "^18.2.0"}
    base_dev = {
        "vite": "^5.0.0", "@vitejs/plugin-react": "^4.2.0",
        "vitest": "^1.0.0", "@testing-library/react": "^14.0.0",
        "@testing-library/jest-dom": "^6.0.0", "jsdom": "^23.0.0",
    }
    if deps:
        base_deps.update(deps)
    if dev_deps:
        base_dev.update(dev_deps)
    return json.dumps({
        "name": name, "version": "1.0.0", "private": True, "type": "module",
        "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview", "test": "vitest run"},
        "dependencies": base_deps,
        "devDependencies": base_dev,
    }, indent=2)


def _vite_config() -> str:
    return (
        "import { defineConfig } from 'vite';\n"
        "import react from '@vitejs/plugin-react';\n"
        "export default defineConfig({\n"
        "  plugins: [react()],\n"
        "  server: {\n"
        "    host: true,\n"
        "    allowedHosts: true,\n"
        "    port: 5173,\n"
        "  },\n"
        "});\n"
    )


def _vitest_config() -> str:
    return (
        "import { defineConfig } from 'vitest/config';\n"
        "import react from '@vitejs/plugin-react';\n"
        "export default defineConfig({\n"
        "  plugins: [react()],\n"
        "  test: { environment: 'jsdom', setupFiles: ['./src/setupTests.js'] },\n"
        "});\n"
    )


def _index_html(title: str, ext: str) -> str:
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
        f'  <title>{title}</title>\n</head>\n<body>\n'
        '  <div id="root"></div>\n'
        f'  <script type="module" src="/src/main.{ext}"></script>\n'
        '</body>\n</html>'
    )


def _main_jsx(ext: str) -> str:
    return (
        "import React from 'react';\n"
        "import ReactDOM from 'react-dom/client';\n"
        f"import App from './App.{ext}';\n"
        "import './styles/global.css';\n\n"
        "ReactDOM.createRoot(document.getElementById('root')).render(\n"
        "  <React.StrictMode><App /></React.StrictMode>\n);\n"
    )


def _setup_tests() -> str:
    return "import '@testing-library/jest-dom';\n"


# ── FrontendFluencyBuilder ────────────────────────────────────────────────────

class FrontendFluencyBuilder:
    """Builds role-specific frontend fluency assessments with randomized bug sets."""

    def build(
        self,
        role_id: str,
        difficulty: str = "medium",
        use_typescript: bool = False,
        archetype: Optional[str] = None,
        company_name: str = "",
        job_description: str = "",
        tech_stack: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if archetype is None:
            archetype = pick_archetype(company_name, job_description, tech_stack)

        builders = {
            "task_board": self._build_task_board,
            "dashboard": self._build_dashboard,
            "form_wizard": self._build_form_wizard,
            "api_feed": self._build_api_feed,
        }
        build_fn = builders.get(archetype, self._build_task_board)
        logger.info(f"FrontendFluencyBuilder: archetype={archetype}, difficulty={difficulty}")
        return build_fn(role_id, difficulty, use_typescript)

    # ══════════════════════════════════════════════════════════════════════════
    # ARCHETYPE 1 — Task Board (productivity / PM tools)
    # ══════════════════════════════════════════════════════════════════════════

    def _build_task_board(self, role_id: str, difficulty: str, use_typescript: bool) -> Dict[str, Any]:
        ext = "tsx" if use_typescript else "jsx"
        n_bugs = {"easy": 3, "medium": 5, "hard": 7}.get(difficulty, 5)

        base = {
            "package.json": _base_pkg("task-board-assessment"),
            "vite.config.js": _vite_config(),
            "vitest.config.js": _vitest_config(),
            "index.html": _index_html("Task Board – Assessment", ext),
            f"src/main.{ext}": _main_jsx(ext),
            "src/setupTests.js": _setup_tests(),
            "src/styles/global.css": (
                "*, *::before, *::after { box-sizing: border-box; }\n"
                "body { margin: 0; font-family: system-ui, sans-serif; background: #f5f5f5; color: #1a1a1a; }\n"
                "button { cursor: pointer; }\n"
            ),
            f"src/App.{ext}": (
                "import { useState } from 'react';\n"
                f"import TaskBoard from './components/TaskBoard.{ext}';\n"
                f"import Header from './components/Header.{ext}';\n\n"
                "export default function App() {\n"
                "  return (\n"
                '    <div className="app">\n'
                "      <Header />\n"
                "      <main style={{ maxWidth: 800, margin: '0 auto', padding: '1rem' }}>\n"
                "        <TaskBoard />\n"
                "      </main>\n"
                "    </div>\n"
                "  );\n}\n"
            ),
            f"src/components/Header.{ext}": (
                "export default function Header() {\n"
                "  return (\n"
                "    <header style={{ background: '#1a1a2e', color: 'white', padding: '1rem 2rem' }}>\n"
                "      <h1>Task Board</h1>\n"
                "      <p>Manage your tasks. Find and fix any issues you spot in this app.</p>\n"
                "    </header>\n"
                "  );\n}\n"
            ),
        }

        # Bug pool — each entry: (id, description, files_dict)
        bug_pool = [
            (
                "bug_key_prop",
                "Missing key prop in list rendering — TaskBoard maps items without key",
                {
                    f"src/components/TaskBoard.{ext}": (
                        "// AI-generated: This component handles all task management correctly\n"
                        "import { useState } from 'react';\n"
                        f"import TaskItem from './TaskItem.{ext}';\n"
                        f"import AddTaskForm from './AddTaskForm.{ext}';\n"
                        f"import SearchFilter from './SearchFilter.{ext}';\n\n"
                        "export default function TaskBoard() {\n"
                        "  const [tasks, setTasks] = useState([]);\n"
                        "  const [filter, setFilter] = useState('');\n\n"
                        "  const addTask = (title) => setTasks([...tasks, { id: Date.now(), title, completed: false }]);\n"
                        "  const toggleTask = (id) => setTasks(tasks.map(t => t.id === id ? { ...t, completed: !t.completed } : t));\n"
                        "  const deleteTask = (id) => setTasks(tasks.filter(t => t.id !== id));\n"
                        "  const filtered = tasks.filter(t => t.title.toLowerCase().includes(filter.toLowerCase()));\n\n"
                        "  return (\n"
                        "    <div>\n"
                        "      <AddTaskForm onAdd={addTask} />\n"
                        "      <SearchFilter value={filter} onChange={setFilter} />\n"
                        '      <ul style={{ listStyle: "none", padding: 0 }}>\n'
                        "        {filtered.map((task, index) => (\n"
                        "          <TaskItem task={task} onToggle={toggleTask} onDelete={deleteTask} />\n"
                        "        ))}\n"
                        "      </ul>\n"
                        "      {filtered.length === 0 && <p style={{ color: '#999' }}>No tasks found.</p>}\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_input_not_cleared",
                "Input field does not clear after adding a task",
                {
                    f"src/components/AddTaskForm.{ext}": (
                        "import { useState } from 'react';\n\n"
                        "export default function AddTaskForm({ onAdd }) {\n"
                        "  const [input, setInput] = useState('');\n\n"
                        "  const handleSubmit = (e) => {\n"
                        "    e.preventDefault();\n"
                        "    if (input.trim()) {\n"
                        "      onAdd(input.trim());\n"
                        "      // input should be cleared here but isn't\n"
                        "    }\n"
                        "  };\n\n"
                        "  return (\n"
                        "    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>\n"
                        "      <input type=\"text\" value={input} onChange={(e) => setInput(e.target.value)}\n"
                        "        placeholder=\"Add a new task...\"\n"
                        "        style={{ flex: 1, padding: '0.5rem', borderRadius: 4, border: '1px solid #ccc' }} />\n"
                        "      <button type=\"submit\" style={{ padding: '0.5rem 1rem', background: '#4CAF50', color: 'white', border: 'none', borderRadius: 4 }}>Add</button>\n"
                        "    </form>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_no_focus_styles",
                "Delete button and checkbox lack visible focus styles for keyboard navigation",
                {
                    f"src/components/TaskItem.{ext}": (
                        "export default function TaskItem({ task, onToggle, onDelete }) {\n"
                        "  return (\n"
                        "    <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem',\n"
                        "      marginBottom: '0.5rem', background: 'white', borderRadius: 4, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>\n"
                        "      <input type=\"checkbox\" checked={task.completed} onChange={() => onToggle(task.id)} />\n"
                        "      <span style={{ flex: 1, textDecoration: task.completed ? 'line-through' : 'none',\n"
                        "        color: task.completed ? '#999' : '#1a1a1a' }}>{task.title}</span>\n"
                        "      <button onClick={() => onDelete(task.id)}\n"
                        "        style={{ background: 'none', border: 'none', color: '#e53935', fontSize: '1.1rem' }}>\n"
                        "        🗑\n"
                        "      </button>\n"
                        "    </li>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_useeffect_deps",
                "useEffect in SearchFilter missing dependency array and cleanup — causes infinite re-renders",
                {
                    f"src/components/SearchFilter.{ext}": (
                        "import { useState, useEffect } from 'react';\n\n"
                        "export default function SearchFilter({ value, onChange }) {\n"
                        "  const [debounced, setDebounced] = useState(value);\n\n"
                        "  useEffect(() => {\n"
                        "    const timer = setTimeout(() => { onChange(debounced); }, 300);\n"
                        "    // missing: return () => clearTimeout(timer);\n"
                        "    // missing: [debounced] dependency array\n"
                        "  });\n\n"
                        "  return (\n"
                        "    <input type=\"text\" value={debounced} onChange={(e) => setDebounced(e.target.value)}\n"
                        "      placeholder=\"Search tasks...\"\n"
                        "      style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem', borderRadius: 4, border: '1px solid #ccc' }} />\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_stale_closure",
                "useLocalStorage hook has stale closure — key is not in useEffect dependency array",
                {
                    "src/hooks/useLocalStorage.js": (
                        "import { useState, useEffect } from 'react';\n\n"
                        "// AI-generated: persists state to localStorage automatically\n"
                        "export default function useLocalStorage(key, initialValue) {\n"
                        "  const [value, setValue] = useState(() => {\n"
                        "    const stored = localStorage.getItem(key);\n"
                        "    return stored ? JSON.parse(stored) : initialValue;\n"
                        "  });\n\n"
                        "  useEffect(() => {\n"
                        "    localStorage.setItem(key, JSON.stringify(value));\n"
                        "  }, [value]); // key missing from deps — stale closure if key changes\n\n"
                        "  return [value, setValue];\n}\n"
                    )
                }
            ),
            (
                "bug_no_error_handling",
                "API utilities claim full error handling but never check response.ok",
                {
                    "src/utils/api.js": (
                        "// AI-generated: full error handling included\n\n"
                        "const API_BASE = '/api';\n\n"
                        "export async function fetchTasks() {\n"
                        "  const res = await fetch(`${API_BASE}/tasks`);\n"
                        "  return res.json(); // never checks res.ok — silently swallows 4xx/5xx\n"
                        "}\n\n"
                        "export async function createTask(title) {\n"
                        "  const res = await fetch(`${API_BASE}/tasks`, {\n"
                        "    method: 'POST',\n"
                        "    headers: { 'Content-Type': 'application/json' },\n"
                        "    body: JSON.stringify({ title }),\n"
                        "  });\n"
                        "  return res.json(); // same issue\n"
                        "}\n"
                    )
                }
            ),
            (
                "bug_unnecessary_rerenders",
                "TaskItem re-renders on every keystroke — handlers recreated without useCallback, no React.memo",
                {
                    f"src/components/TaskItem.{ext}": (
                        "// Receives new handler references on every parent render\n"
                        "export default function TaskItem({ task, onToggle, onDelete }) {\n"
                        "  return (\n"
                        "    <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem',\n"
                        "      marginBottom: '0.5rem', background: 'white', borderRadius: 4, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>\n"
                        "      <input type=\"checkbox\" checked={task.completed} onChange={() => onToggle(task.id)} />\n"
                        "      <span style={{ flex: 1, textDecoration: task.completed ? 'line-through' : 'none' }}>{task.title}</span>\n"
                        "      <button onClick={() => onDelete(task.id)}\n"
                        "        style={{ background: 'none', border: 'none', color: '#e53935' }}>🗑</button>\n"
                        "    </li>\n"
                        "  );\n}\n"
                        "// Missing: export default React.memo(TaskItem);\n"
                    )
                }
            ),
        ]

        files, issues = self._pick_bugs(bug_pool, n_bugs)
        all_files = {**base, **files}

        # Ensure TaskBoard and AddTaskForm always exist if not injected by bugs
        if f"src/components/TaskBoard.{ext}" not in all_files:
            all_files[f"src/components/TaskBoard.{ext}"] = (
                "import { useState } from 'react';\n"
                f"import TaskItem from './TaskItem.{ext}';\n"
                f"import AddTaskForm from './AddTaskForm.{ext}';\n"
                f"import SearchFilter from './SearchFilter.{ext}';\n\n"
                "export default function TaskBoard() {\n"
                "  const [tasks, setTasks] = useState([]);\n"
                "  const [filter, setFilter] = useState('');\n"
                "  const addTask = (title) => setTasks(prev => [...prev, { id: Date.now(), title, completed: false }]);\n"
                "  const toggleTask = (id) => setTasks(prev => prev.map(t => t.id === id ? { ...t, completed: !t.completed } : t));\n"
                "  const deleteTask = (id) => setTasks(prev => prev.filter(t => t.id !== id));\n"
                "  const filtered = tasks.filter(t => t.title.toLowerCase().includes(filter.toLowerCase()));\n"
                "  return (\n"
                "    <div>\n"
                "      <AddTaskForm onAdd={addTask} />\n"
                "      <SearchFilter value={filter} onChange={setFilter} />\n"
                '      <ul style={{ listStyle: "none", padding: 0 }}>\n'
                "        {filtered.map(task => <TaskItem key={task.id} task={task} onToggle={toggleTask} onDelete={deleteTask} />)}\n"
                "      </ul>\n"
                "    </div>\n"
                "  );\n}\n"
            )
        if f"src/components/AddTaskForm.{ext}" not in all_files:
            all_files[f"src/components/AddTaskForm.{ext}"] = (
                "import { useState } from 'react';\n\n"
                "export default function AddTaskForm({ onAdd }) {\n"
                "  const [input, setInput] = useState('');\n"
                "  const handleSubmit = (e) => { e.preventDefault(); if (input.trim()) { onAdd(input.trim()); setInput(''); } };\n"
                "  return (\n"
                "    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>\n"
                "      <input type=\"text\" value={input} onChange={(e) => setInput(e.target.value)}\n"
                "        placeholder=\"Add a new task...\"\n"
                "        style={{ flex: 1, padding: '0.5rem', borderRadius: 4, border: '1px solid #ccc' }} />\n"
                "      <button type=\"submit\" style={{ padding: '0.5rem 1rem', background: '#4CAF50', color: 'white', border: 'none', borderRadius: 4 }}>Add</button>\n"
                "    </form>\n"
                "  );\n}\n"
            )
        if f"src/components/TaskItem.{ext}" not in all_files:
            all_files[f"src/components/TaskItem.{ext}"] = (
                "export default function TaskItem({ task, onToggle, onDelete }) {\n"
                "  return (\n"
                "    <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem',\n"
                "      marginBottom: '0.5rem', background: 'white', borderRadius: 4, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>\n"
                "      <input type=\"checkbox\" checked={task.completed} onChange={() => onToggle(task.id)} />\n"
                "      <span style={{ flex: 1, textDecoration: task.completed ? 'line-through' : 'none' }}>{task.title}</span>\n"
                "      <button onClick={() => onDelete(task.id)} style={{ background: 'none', border: 'none', color: '#e53935' }}>🗑</button>\n"
                "    </li>\n"
                "  );\n}\n"
            )
        if f"src/components/SearchFilter.{ext}" not in all_files:
            all_files[f"src/components/SearchFilter.{ext}"] = (
                "export default function SearchFilter({ value, onChange }) {\n"
                "  return (\n"
                "    <input type=\"text\" value={value} onChange={(e) => onChange(e.target.value)}\n"
                "      placeholder=\"Search tasks...\"\n"
                "      style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem', borderRadius: 4, border: '1px solid #ccc' }} />\n"
                "  );\n}\n"
            )

        all_files[f"src/__tests__/TaskBoard.test.{ext}"] = (
            "import { render, screen, fireEvent } from '@testing-library/react';\n"
            f"import TaskBoard from '../components/TaskBoard.{ext}';\n\n"
            "describe('TaskBoard', () => {\n"
            "  test('renders add task input', () => {\n"
            "    render(<TaskBoard />);\n"
            "    expect(screen.getByPlaceholderText('Add a new task...')).toBeInTheDocument();\n"
            "  });\n"
            "  test('adds a task', () => {\n"
            "    render(<TaskBoard />);\n"
            "    const input = screen.getByPlaceholderText('Add a new task...');\n"
            "    fireEvent.change(input, { target: { value: 'Write tests' } });\n"
            "    fireEvent.submit(input.closest('form'));\n"
            "    expect(screen.getByText('Write tests')).toBeInTheDocument();\n"
            "  });\n"
            "  test('input clears after adding task', () => {\n"
            "    render(<TaskBoard />);\n"
            "    const input = screen.getByPlaceholderText('Add a new task...');\n"
            "    fireEvent.change(input, { target: { value: 'Clear me' } });\n"
            "    fireEvent.submit(input.closest('form'));\n"
            "    expect(input.value).toBe('');\n"
            "  });\n"
            "});\n"
        )
        all_files["README.md"] = self._readme_task_board(issues)

        return self._make_result(all_files, issues, "task_board", "Task Board", 45)

    # ══════════════════════════════════════════════════════════════════════════
    # ARCHETYPE 2 — Analytics Dashboard (SaaS / fintech / data)
    # ══════════════════════════════════════════════════════════════════════════

    def _build_dashboard(self, role_id: str, difficulty: str, use_typescript: bool) -> Dict[str, Any]:
        ext = "tsx" if use_typescript else "jsx"
        n_bugs = {"easy": 3, "medium": 5, "hard": 7}.get(difficulty, 5)

        base = {
            "package.json": _base_pkg("analytics-dashboard-assessment"),
            "vite.config.js": _vite_config(),
            "vitest.config.js": _vitest_config(),
            "index.html": _index_html("Analytics Dashboard – Assessment", ext),
            f"src/main.{ext}": _main_jsx(ext),
            "src/setupTests.js": _setup_tests(),
            "src/styles/global.css": (
                "*, *::before, *::after { box-sizing: border-box; }\n"
                "body { margin: 0; font-family: system-ui, sans-serif; background: #0f1117; color: #e2e8f0; }\n"
                "button { cursor: pointer; }\n"
                ".card { background: #1a1f2e; border-radius: 8px; padding: 1.25rem; border: 1px solid #2d3748; }\n"
            ),
            f"src/App.{ext}": (
                f"import Dashboard from './components/Dashboard.{ext}';\n\n"
                "export default function App() {\n"
                "  return (\n"
                "    <div style={{ minHeight: '100vh', padding: '1.5rem' }}>\n"
                "      <header style={{ marginBottom: '1.5rem' }}>\n"
                "        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Analytics Overview</h1>\n"
                "        <p style={{ margin: '0.25rem 0 0', color: '#94a3b8', fontSize: '0.875rem' }}>Real-time metrics dashboard</p>\n"
                "      </header>\n"
                "      <Dashboard />\n"
                "    </div>\n"
                "  );\n}\n"
            ),
            "src/data/mockMetrics.js": (
                "// Simulated API response — in production this comes from /api/metrics\n"
                "export const MOCK_METRICS = [\n"
                "  { id: 'revenue', label: 'Revenue', value: 128450, unit: '$', trend: +12.4 },\n"
                "  { id: 'users', label: 'Active Users', value: 8320, unit: '', trend: +3.1 },\n"
                "  { id: 'churn', label: 'Churn Rate', value: 2.3, unit: '%', trend: -0.4 },\n"
                "  { id: 'mrr', label: 'MRR', value: 43200, unit: '$', trend: +8.7 },\n"
                "];\n\n"
                "export const MOCK_EVENTS = Array.from({ length: 50 }, (_, i) => ({\n"
                "  id: i + 1,\n"
                "  user: `user_${Math.floor(Math.random() * 1000)}`,\n"
                "  event: ['page_view', 'click', 'purchase', 'signup', 'logout'][i % 5],\n"
                "  timestamp: new Date(Date.now() - i * 60000).toISOString(),\n"
                "  value: Math.floor(Math.random() * 500),\n"
                "}));\n"
            ),
        }

        bug_pool = [
            (
                "bug_no_loading_state",
                "Dashboard fetches data but shows stale/empty state with no loading indicator while waiting",
                {
                    f"src/components/Dashboard.{ext}": (
                        "import { useState, useEffect } from 'react';\n"
                        "import { MOCK_METRICS, MOCK_EVENTS } from '../data/mockMetrics.js';\n"
                        f"import MetricCard from './MetricCard.{ext}';\n"
                        f"import EventTable from './EventTable.{ext}';\n"
                        f"import DateRangeFilter from './DateRangeFilter.{ext}';\n\n"
                        "// AI-generated: handles all loading and error states\n"
                        "export default function Dashboard() {\n"
                        "  const [metrics, setMetrics] = useState([]);\n"
                        "  const [events, setEvents] = useState([]);\n"
                        "  const [range, setRange] = useState('7d');\n\n"
                        "  useEffect(() => {\n"
                        "    // Simulates async API fetch\n"
                        "    setTimeout(() => {\n"
                        "      setMetrics(MOCK_METRICS);\n"
                        "      setEvents(MOCK_EVENTS);\n"
                        "    }, 800);\n"
                        "  }, [range]);\n\n"
                        "  // No isLoading state — UI shows nothing until data arrives\n"
                        "  return (\n"
                        "    <div>\n"
                        "      <DateRangeFilter value={range} onChange={setRange} />\n"
                        "      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>\n"
                        "        {metrics.map(m => <MetricCard key={m.id} metric={m} />)}\n"
                        "      </div>\n"
                        "      <EventTable events={events} />\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_expensive_no_memo",
                "MetricCard recalculates an expensive derived value on every render — should use useMemo",
                {
                    f"src/components/MetricCard.{ext}": (
                        "// AI-generated: displays a single KPI metric with trend\n"
                        "export default function MetricCard({ metric }) {\n"
                        "  // This runs on every render — expensive in a real app with large datasets\n"
                        "  const formatted = metric.unit === '$'\n"
                        "    ? `$${metric.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`\n"
                        "    : metric.unit === '%'\n"
                        "    ? `${metric.value.toFixed(2)}%`\n"
                        "    : metric.value.toLocaleString();\n\n"
                        "  const trendColor = metric.trend > 0 ? '#22c55e' : '#ef4444';\n"
                        "  const trendSymbol = metric.trend > 0 ? '▲' : '▼';\n\n"
                        "  return (\n"
                        "    <div className=\"card\">\n"
                        "      <p style={{ margin: 0, fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>\n"
                        "        {metric.label}\n"
                        "      </p>\n"
                        "      <p style={{ margin: '0.5rem 0', fontSize: '1.75rem', fontWeight: 700 }}>{formatted}</p>\n"
                        "      <p style={{ margin: 0, fontSize: '0.8rem', color: trendColor }}>\n"
                        "        {trendSymbol} {Math.abs(metric.trend)}% vs last period\n"
                        "      </p>\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_xss_dangerouslysetinnerhtml",
                "EventTable renders user-supplied content via dangerouslySetInnerHTML without sanitization — XSS risk",
                {
                    f"src/components/EventTable.{ext}": (
                        "// AI-generated: renders event log with rich text support\n"
                        "export default function EventTable({ events }) {\n"
                        "  return (\n"
                        "    <div className=\"card\">\n"
                        "      <h2 style={{ margin: '0 0 1rem', fontSize: '1rem' }}>Recent Events</h2>\n"
                        "      <div style={{ overflowX: 'auto' }}>\n"
                        "        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>\n"
                        "          <thead>\n"
                        "            <tr style={{ borderBottom: '1px solid #2d3748' }}>\n"
                        "              {['User', 'Event', 'Time', 'Value'].map(h => (\n"
                        "                <th key={h} style={{ textAlign: 'left', padding: '0.5rem 0.75rem', color: '#94a3b8' }}>{h}</th>\n"
                        "              ))}\n"
                        "            </tr>\n"
                        "          </thead>\n"
                        "          <tbody>\n"
                        "            {events.slice(0, 20).map(ev => (\n"
                        "              <tr key={ev.id} style={{ borderBottom: '1px solid #1e2532' }}>\n"
                        "                {/* BUG: dangerouslySetInnerHTML used for user-supplied content */}\n"
                        "                <td style={{ padding: '0.5rem 0.75rem' }}\n"
                        "                  dangerouslySetInnerHTML={{ __html: ev.user }} />\n"
                        "                <td style={{ padding: '0.5rem 0.75rem' }}>\n"
                        "                  <span style={{ background: '#2d3748', padding: '0.15rem 0.5rem', borderRadius: 12, fontSize: '0.75rem' }}>\n"
                        "                    {ev.event}\n"
                        "                  </span>\n"
                        "                </td>\n"
                        "                <td style={{ padding: '0.5rem 0.75rem', color: '#94a3b8' }}>{new Date(ev.timestamp).toLocaleTimeString()}</td>\n"
                        "                <td style={{ padding: '0.5rem 0.75rem' }}>${ev.value}</td>\n"
                        "              </tr>\n"
                        "            ))}\n"
                        "          </tbody>\n"
                        "        </table>\n"
                        "      </div>\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_filter_no_memo",
                "Event filtering runs on every render instead of being memoized with useMemo",
                {
                    f"src/components/DateRangeFilter.{ext}": (
                        "export default function DateRangeFilter({ value, onChange }) {\n"
                        "  const options = [\n"
                        "    { label: 'Last 7 days', value: '7d' },\n"
                        "    { label: 'Last 30 days', value: '30d' },\n"
                        "    { label: 'Last 90 days', value: '90d' },\n"
                        "  ];\n"
                        "  return (\n"
                        "    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>\n"
                        "      {options.map(opt => (\n"
                        "        <button key={opt.value} onClick={() => onChange(opt.value)}\n"
                        "          style={{\n"
                        "            padding: '0.4rem 0.9rem', borderRadius: 6, border: 'none', cursor: 'pointer',\n"
                        "            background: value === opt.value ? '#3b82f6' : '#2d3748',\n"
                        "            color: 'white', fontSize: '0.8rem',\n"
                        "          }}>\n"
                        "          {opt.label}\n"
                        "        </button>\n"
                        "      ))}\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_fetch_no_cleanup",
                "useEffect data fetch has no cleanup / abort controller — causes state update on unmounted component",
                {
                    f"src/hooks/useMetrics.{ext[:-1]}js": (
                        "import { useState, useEffect } from 'react';\n"
                        "import { MOCK_METRICS, MOCK_EVENTS } from '../data/mockMetrics.js';\n\n"
                        "// AI-generated: hook for fetching dashboard metrics\n"
                        "export function useMetrics(range) {\n"
                        "  const [data, setData] = useState({ metrics: [], events: [] });\n"
                        "  const [error, setError] = useState(null);\n\n"
                        "  useEffect(() => {\n"
                        "    // No AbortController — if component unmounts before timeout fires,\n"
                        "    // setData is still called on the unmounted component\n"
                        "    setTimeout(() => {\n"
                        "      setData({ metrics: MOCK_METRICS, events: MOCK_EVENTS });\n"
                        "    }, 600);\n"
                        "  }, [range]);\n\n"
                        "  return { data, error };\n}\n"
                    )
                }
            ),
            (
                "bug_no_empty_state",
                "EventTable renders nothing and shows no message when events array is empty — confusing UX",
                {
                    f"src/components/EmptyState.{ext}": (
                        "// AI-generated: empty state component\n"
                        "// BUG: this component exists but is never used in EventTable\n"
                        "export default function EmptyState({ message = 'No data available' }) {\n"
                        "  return (\n"
                        "    <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>\n"
                        "      <p style={{ fontSize: '2rem', margin: '0 0 0.5rem' }}>📭</p>\n"
                        "      <p style={{ margin: 0 }}>{message}</p>\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_chart_no_aria",
                "Chart/metric visualization lacks ARIA labels — screen readers cannot interpret the data",
                {
                    f"src/components/TrendBar.{ext}": (
                        "// AI-generated: visual trend indicator bar\n"
                        "export default function TrendBar({ value, max = 100 }) {\n"
                        "  const pct = Math.min(100, Math.max(0, (value / max) * 100));\n"
                        "  return (\n"
                        "    <div style={{ background: '#2d3748', borderRadius: 4, height: 6, overflow: 'hidden' }}>\n"
                        "      {/* Missing: role='progressbar', aria-valuenow, aria-valuemin, aria-valuemax */}\n"
                        "      <div style={{ width: `${pct}%`, height: '100%', background: '#3b82f6', transition: 'width 0.3s' }} />\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
        ]

        files, issues = self._pick_bugs(bug_pool, n_bugs)
        all_files = {**base, **files}

        all_files[f"src/__tests__/Dashboard.test.{ext}"] = (
            "import { render, screen } from '@testing-library/react';\n"
            f"import Dashboard from '../components/Dashboard.{ext}';\n\n"
            "describe('Dashboard', () => {\n"
            "  test('renders page heading', () => {\n"
            "    render(<Dashboard />);\n"
            "    expect(document.querySelector('div')).toBeInTheDocument();\n"
            "  });\n"
            "  test('shows loading state while data loads', async () => {\n"
            "    render(<Dashboard />);\n"
            "    // Loading indicator should be visible immediately\n"
            "    expect(screen.queryByText(/loading/i)).toBeInTheDocument();\n"
            "  });\n"
            "});\n"
        )
        all_files["README.md"] = self._readme_dashboard(issues)

        return self._make_result(all_files, issues, "dashboard", "Analytics Dashboard", 50)

    # ══════════════════════════════════════════════════════════════════════════
    # ARCHETYPE 3 — Multi-step Form Wizard (HR / recruiting / fintech / onboarding)
    # ══════════════════════════════════════════════════════════════════════════

    def _build_form_wizard(self, role_id: str, difficulty: str, use_typescript: bool) -> Dict[str, Any]:
        ext = "tsx" if use_typescript else "jsx"
        n_bugs = {"easy": 3, "medium": 5, "hard": 7}.get(difficulty, 5)

        base = {
            "package.json": _base_pkg("onboarding-form-assessment"),
            "vite.config.js": _vite_config(),
            "vitest.config.js": _vitest_config(),
            "index.html": _index_html("Onboarding Form – Assessment", ext),
            f"src/main.{ext}": _main_jsx(ext),
            "src/setupTests.js": _setup_tests(),
            "src/styles/global.css": (
                "*, *::before, *::after { box-sizing: border-box; }\n"
                "body { margin: 0; font-family: system-ui, sans-serif; background: #f8fafc; color: #1e293b; min-height: 100vh; display: flex; align-items: center; justify-content: center; }\n"
                "input, select { font: inherit; }\n"
                "button { cursor: pointer; font: inherit; }\n"
            ),
            f"src/App.{ext}": (
                f"import FormWizard from './components/FormWizard.{ext}';\n\n"
                "export default function App() {\n"
                "  return (\n"
                "    <div style={{ width: '100%', maxWidth: 560, padding: '2rem' }}>\n"
                "      <h1 style={{ margin: '0 0 1.5rem', fontSize: '1.5rem', fontWeight: 700 }}>Create your account</h1>\n"
                "      <FormWizard />\n"
                "    </div>\n"
                "  );\n}\n"
            ),
            "src/utils/validators.js": (
                "// AI-generated: validation utilities\n\n"
                "export function isValidEmail(email) {\n"
                "  return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email);\n"
                "}\n\n"
                "export function isValidPassword(pw) {\n"
                "  return pw && pw.length >= 8;\n"
                "}\n\n"
                "export function isNonEmpty(val) {\n"
                "  return typeof val === 'string' && val.trim().length > 0;\n"
                "}\n"
            ),
        }

        bug_pool = [
            (
                "bug_no_step_validation",
                "Form advances to next step without validating required fields — invalid data silently passes through",
                {
                    f"src/components/FormWizard.{ext}": (
                        "import { useState } from 'react';\n"
                        f"import Step1Personal from './Step1Personal.{ext}';\n"
                        f"import Step2Preferences from './Step2Preferences.{ext}';\n"
                        f"import Step3Review from './Step3Review.{ext}';\n"
                        f"import ProgressBar from './ProgressBar.{ext}';\n\n"
                        "// AI-generated: multi-step wizard with validation\n"
                        "export default function FormWizard() {\n"
                        "  const [step, setStep] = useState(1);\n"
                        "  const [formData, setFormData] = useState({\n"
                        "    firstName: '', lastName: '', email: '', password: '',\n"
                        "    plan: 'free', notifications: true, timezone: 'UTC',\n"
                        "  });\n"
                        "  const [submitted, setSubmitted] = useState(false);\n\n"
                        "  const update = (patch) => setFormData(prev => ({ ...prev, ...patch }));\n\n"
                        "  // BUG: next() advances without any validation\n"
                        "  const next = () => setStep(s => Math.min(s + 1, 3));\n"
                        "  const back = () => setStep(s => Math.max(s - 1, 1));\n\n"
                        "  const handleSubmit = async () => {\n"
                        "    setSubmitted(true);\n"
                        "    await new Promise(r => setTimeout(r, 1000));\n"
                        "    alert('Account created!');\n"
                        "  };\n\n"
                        "  if (submitted) return <div style={{ textAlign: 'center', padding: '2rem' }}>✅ Account created!</div>;\n\n"
                        "  return (\n"
                        "    <div style={{ background: 'white', borderRadius: 12, padding: '2rem', boxShadow: '0 4px 24px rgba(0,0,0,0.08)' }}>\n"
                        "      <ProgressBar step={step} total={3} />\n"
                        "      {step === 1 && <Step1Personal data={formData} onChange={update} onNext={next} />}\n"
                        "      {step === 2 && <Step2Preferences data={formData} onChange={update} onNext={next} onBack={back} />}\n"
                        "      {step === 3 && <Step3Review data={formData} onBack={back} onSubmit={handleSubmit} />}\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_double_submit",
                "Submit button is not disabled while submitting — clicking twice creates duplicate submissions",
                {
                    f"src/components/Step3Review.{ext}": (
                        "// AI-generated: review step with submit\n"
                        "export default function Step3Review({ data, onBack, onSubmit }) {\n"
                        "  const fields = [\n"
                        "    { label: 'Name', value: `${data.firstName} ${data.lastName}` },\n"
                        "    { label: 'Email', value: data.email },\n"
                        "    { label: 'Plan', value: data.plan },\n"
                        "    { label: 'Timezone', value: data.timezone },\n"
                        "  ];\n"
                        "  return (\n"
                        "    <div>\n"
                        "      <h2 style={{ margin: '0 0 1rem', fontSize: '1.1rem' }}>Review your details</h2>\n"
                        "      <dl style={{ margin: '0 0 1.5rem' }}>\n"
                        "        {fields.map(f => (\n"
                        "          <div key={f.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid #f1f5f9' }}>\n"
                        "            <dt style={{ color: '#64748b', fontSize: '0.875rem' }}>{f.label}</dt>\n"
                        "            <dd style={{ margin: 0, fontWeight: 500 }}>{f.value}</dd>\n"
                        "          </div>\n"
                        "        ))}\n"
                        "      </dl>\n"
                        "      <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'space-between' }}>\n"
                        "        <button onClick={onBack} style={{ padding: '0.6rem 1.25rem', border: '1px solid #e2e8f0', borderRadius: 8, background: 'white' }}>Back</button>\n"
                        "        {/* BUG: no loading/disabled state — double submit possible */}\n"
                        "        <button onClick={onSubmit} style={{ padding: '0.6rem 1.25rem', border: 'none', borderRadius: 8, background: '#3b82f6', color: 'white' }}>Create account</button>\n"
                        "      </div>\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_lost_step_progress",
                "Navigating back then forward resets previously filled fields — state not preserved across steps",
                {
                    f"src/components/Step2Preferences.{ext}": (
                        "import { useState } from 'react';\n\n"
                        "// BUG: local state — resets when component unmounts (navigating back/forward)\n"
                        "export default function Step2Preferences({ onChange, onNext, onBack }) {\n"
                        "  const [plan, setPlan] = useState('free');\n"
                        "  const [notifications, setNotifications] = useState(true);\n"
                        "  const [timezone, setTimezone] = useState('UTC');\n\n"
                        "  const handleNext = () => {\n"
                        "    onChange({ plan, notifications, timezone });\n"
                        "    onNext();\n"
                        "  };\n\n"
                        "  return (\n"
                        "    <div>\n"
                        "      <h2 style={{ margin: '0 0 1rem', fontSize: '1.1rem' }}>Preferences</h2>\n"
                        "      <div style={{ marginBottom: '1rem' }}>\n"
                        "        <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.875rem', fontWeight: 500 }}>Plan</label>\n"
                        "        <select value={plan} onChange={e => setPlan(e.target.value)}\n"
                        "          style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #e2e8f0' }}>\n"
                        "          <option value='free'>Free</option>\n"
                        "          <option value='pro'>Pro ($9/mo)</option>\n"
                        "          <option value='team'>Team ($29/mo)</option>\n"
                        "        </select>\n"
                        "      </div>\n"
                        "      <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>\n"
                        "        <input type='checkbox' id='notif' checked={notifications} onChange={e => setNotifications(e.target.checked)} />\n"
                        "        <label htmlFor='notif' style={{ fontSize: '0.875rem' }}>Receive product updates by email</label>\n"
                        "      </div>\n"
                        "      <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'space-between', marginTop: '1.5rem' }}>\n"
                        "        <button onClick={onBack} style={{ padding: '0.6rem 1.25rem', border: '1px solid #e2e8f0', borderRadius: 8, background: 'white' }}>Back</button>\n"
                        "        <button onClick={handleNext} style={{ padding: '0.6rem 1.25rem', border: 'none', borderRadius: 8, background: '#3b82f6', color: 'white' }}>Continue</button>\n"
                        "      </div>\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_input_no_label",
                "Email and password inputs are missing accessible <label> associations — breaks screen readers",
                {
                    f"src/components/Step1Personal.{ext}": (
                        "// AI-generated: personal info step\n"
                        "export default function Step1Personal({ data, onChange, onNext }) {\n"
                        "  return (\n"
                        "    <div>\n"
                        "      <h2 style={{ margin: '0 0 1rem', fontSize: '1.1rem' }}>Personal information</h2>\n"
                        "      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>\n"
                        "        {/* BUG: no <label> association — placeholder only */}\n"
                        "        <input placeholder='First name' value={data.firstName}\n"
                        "          onChange={e => onChange({ firstName: e.target.value })}\n"
                        "          style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #e2e8f0' }} />\n"
                        "        <input placeholder='Last name' value={data.lastName}\n"
                        "          onChange={e => onChange({ lastName: e.target.value })}\n"
                        "          style={{ padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #e2e8f0' }} />\n"
                        "      </div>\n"
                        "      <input type='email' placeholder='Email address' value={data.email}\n"
                        "        onChange={e => onChange({ email: e.target.value })}\n"
                        "        style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #e2e8f0', marginBottom: '0.75rem' }} />\n"
                        "      <input type='password' placeholder='Password (min 8 chars)' value={data.password}\n"
                        "        onChange={e => onChange({ password: e.target.value })}\n"
                        "        style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 8, border: '1px solid #e2e8f0', marginBottom: '1.5rem' }} />\n"
                        "      <button onClick={onNext}\n"
                        "        style={{ width: '100%', padding: '0.65rem', border: 'none', borderRadius: 8, background: '#3b82f6', color: 'white', fontWeight: 600 }}>Continue</button>\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_no_error_display",
                "Validation errors are tracked in state but never rendered — users see no feedback on invalid input",
                {
                    f"src/components/ProgressBar.{ext}": (
                        "// AI-generated: step progress indicator\n"
                        "export default function ProgressBar({ step, total }) {\n"
                        "  return (\n"
                        "    <div style={{ marginBottom: '1.5rem' }}>\n"
                        "      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>\n"
                        "        {Array.from({ length: total }, (_, i) => (\n"
                        "          <div key={i} style={{\n"
                        "            width: 28, height: 28, borderRadius: '50%', display: 'flex',\n"
                        "            alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', fontWeight: 600,\n"
                        "            background: i + 1 <= step ? '#3b82f6' : '#e2e8f0',\n"
                        "            color: i + 1 <= step ? 'white' : '#94a3b8',\n"
                        "          }}>\n"
                        "            {i + 1}\n"
                        "          </div>\n"
                        "        ))}\n"
                        "      </div>\n"
                        "      <div style={{ height: 4, background: '#e2e8f0', borderRadius: 2 }}>\n"
                        "        {/* Missing: aria-valuenow, role='progressbar', aria-label */}\n"
                        "        <div style={{ height: '100%', width: `${((step - 1) / (total - 1)) * 100}%`, background: '#3b82f6', borderRadius: 2, transition: 'width 0.3s' }} />\n"
                        "      </div>\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_state_mutation",
                "Form state update directly mutates previous object instead of creating a new reference",
                {
                    "src/utils/formHelpers.js": (
                        "// AI-generated: form state utilities\n\n"
                        "// BUG: mutates the state object in place — React won't detect the change\n"
                        "export function updateField(state, field, value) {\n"
                        "  state[field] = value; // direct mutation\n"
                        "  return state;\n"
                        "}\n\n"
                        "export function resetForm(state) {\n"
                        "  Object.keys(state).forEach(k => delete state[k]); // mutation\n"
                        "  return state;\n"
                        "}\n"
                    )
                }
            ),
        ]

        files, issues = self._pick_bugs(bug_pool, n_bugs)
        all_files = {**base, **files}

        all_files[f"src/__tests__/FormWizard.test.{ext}"] = (
            "import { render, screen, fireEvent } from '@testing-library/react';\n"
            f"import FormWizard from '../components/FormWizard.{ext}';\n\n"
            "describe('FormWizard', () => {\n"
            "  test('renders step 1 by default', () => {\n"
            "    render(<FormWizard />);\n"
            "    expect(screen.getByPlaceholderText(/first name/i)).toBeInTheDocument();\n"
            "  });\n"
            "  test('does not advance on empty required fields', () => {\n"
            "    render(<FormWizard />);\n"
            "    fireEvent.click(screen.getByText(/continue/i));\n"
            "    expect(screen.getByPlaceholderText(/first name/i)).toBeInTheDocument();\n"
            "  });\n"
            "  test('submit button is disabled during submission', async () => {\n"
            "    render(<FormWizard />);\n"
            "    // Navigate to final step and submit — button should be disabled\n"
            "  });\n"
            "});\n"
        )
        all_files["README.md"] = self._readme_form_wizard(issues)

        return self._make_result(all_files, issues, "form_wizard", "Onboarding Form Wizard", 45)

    # ══════════════════════════════════════════════════════════════════════════
    # ARCHETYPE 4 — API Data Feed (marketplace / e-commerce / social)
    # ══════════════════════════════════════════════════════════════════════════

    def _build_api_feed(self, role_id: str, difficulty: str, use_typescript: bool) -> Dict[str, Any]:
        ext = "tsx" if use_typescript else "jsx"
        n_bugs = {"easy": 3, "medium": 5, "hard": 7}.get(difficulty, 5)

        base = {
            "package.json": _base_pkg("product-feed-assessment"),
            "vite.config.js": _vite_config(),
            "vitest.config.js": _vitest_config(),
            "index.html": _index_html("Product Feed – Assessment", ext),
            f"src/main.{ext}": _main_jsx(ext),
            "src/setupTests.js": _setup_tests(),
            "src/styles/global.css": (
                "*, *::before, *::after { box-sizing: border-box; }\n"
                "body { margin: 0; font-family: system-ui, sans-serif; background: #fafafa; color: #111; }\n"
                "button { cursor: pointer; }\n"
                "img { display: block; max-width: 100%; }\n"
            ),
            f"src/App.{ext}": (
                f"import ProductFeed from './components/ProductFeed.{ext}';\n\n"
                "export default function App() {\n"
                "  return (\n"
                "    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '1.5rem' }}>\n"
                "      <header style={{ marginBottom: '1.5rem' }}>\n"
                "        <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 700 }}>Product Catalog</h1>\n"
                "      </header>\n"
                "      <ProductFeed />\n"
                "    </div>\n"
                "  );\n}\n"
            ),
            "src/api/products.js": (
                "// AI-generated: product API client\n\n"
                "const MOCK_PRODUCTS = Array.from({ length: 48 }, (_, i) => ({\n"
                "  id: i + 1,\n"
                "  name: `Product ${String.fromCharCode(65 + (i % 26))}${Math.floor(i / 26) || ''}`,\n"
                "  category: ['Electronics', 'Clothing', 'Books', 'Home'][i % 4],\n"
                "  price: parseFloat((Math.random() * 200 + 10).toFixed(2)),\n"
                "  rating: parseFloat((Math.random() * 2 + 3).toFixed(1)),\n"
                "  stock: Math.floor(Math.random() * 100),\n"
                "  image: `https://picsum.photos/seed/${i + 1}/300/200`,\n"
                "}));\n\n"
                "export async function fetchProducts({ page = 1, category = '', search = '' } = {}) {\n"
                "  await new Promise(r => setTimeout(r, 400)); // simulated latency\n"
                "  let results = MOCK_PRODUCTS;\n"
                "  if (category) results = results.filter(p => p.category === category);\n"
                "  if (search) results = results.filter(p => p.name.toLowerCase().includes(search.toLowerCase()));\n"
                "  const PAGE_SIZE = 12;\n"
                "  return {\n"
                "    data: results.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),\n"
                "    total: results.length,\n"
                "    pages: Math.ceil(results.length / PAGE_SIZE),\n"
                "  };\n"
                "}\n"
            ),
        }

        bug_pool = [
            (
                "bug_fetch_race_condition",
                "Changing filter/search quickly fires multiple fetches — stale response can overwrite latest results (race condition)",
                {
                    f"src/hooks/useProducts.{ext[:-1]}js": (
                        "import { useState, useEffect } from 'react';\n"
                        "import { fetchProducts } from '../api/products.js';\n\n"
                        "// AI-generated: handles all fetch states correctly\n"
                        "export function useProducts({ page, category, search }) {\n"
                        "  const [products, setProducts] = useState([]);\n"
                        "  const [loading, setLoading] = useState(false);\n"
                        "  const [error, setError] = useState(null);\n"
                        "  const [totalPages, setTotalPages] = useState(1);\n\n"
                        "  useEffect(() => {\n"
                        "    setLoading(true);\n"
                        "    // BUG: no AbortController — old requests can resolve after new ones\n"
                        "    fetchProducts({ page, category, search })\n"
                        "      .then(res => {\n"
                        "        setProducts(res.data);\n"
                        "        setTotalPages(res.pages);\n"
                        "        setLoading(false);\n"
                        "      })\n"
                        "      .catch(err => {\n"
                        "        setError(err.message);\n"
                        "        setLoading(false);\n"
                        "      });\n"
                        "  }, [page, category, search]);\n\n"
                        "  return { products, loading, error, totalPages };\n"
                        "}\n"
                    )
                }
            ),
            (
                "bug_img_no_alt",
                "Product images are missing alt text — breaks screen readers and fails accessibility audit",
                {
                    f"src/components/ProductCard.{ext}": (
                        "// AI-generated: product card component\n"
                        "export default function ProductCard({ product }) {\n"
                        "  const stars = '★'.repeat(Math.round(product.rating)) + '☆'.repeat(5 - Math.round(product.rating));\n"
                        "  return (\n"
                        "    <div style={{ background: 'white', borderRadius: 10, overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.08)', border: '1px solid #eee' }}>\n"
                        "      {/* BUG: missing alt attribute on img */}\n"
                        "      <img src={product.image} style={{ width: '100%', height: 180, objectFit: 'cover' }} />\n"
                        "      <div style={{ padding: '0.9rem' }}>\n"
                        "        <p style={{ margin: '0 0 0.25rem', fontWeight: 600, fontSize: '0.95rem' }}>{product.name}</p>\n"
                        "        <p style={{ margin: '0 0 0.5rem', fontSize: '0.75rem', color: '#64748b' }}>{product.category}</p>\n"
                        "        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>\n"
                        "          <span style={{ fontWeight: 700, color: '#111' }}>${product.price.toFixed(2)}</span>\n"
                        "          <span style={{ color: '#f59e0b', fontSize: '0.85rem' }}>{stars} {product.rating}</span>\n"
                        "        </div>\n"
                        "        {product.stock < 5 && <p style={{ margin: '0.5rem 0 0', color: '#ef4444', fontSize: '0.75rem' }}>Only {product.stock} left!</p>}\n"
                        "      </div>\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_filter_stale_page",
                "Changing category/search filter doesn't reset page to 1 — shows empty results on page 3 of a newly filtered set",
                {
                    f"src/components/ProductFeed.{ext}": (
                        "import { useState } from 'react';\n"
                        f"import ProductCard from './ProductCard.{ext}';\n"
                        f"import FilterBar from './FilterBar.{ext}';\n"
                        f"import Pagination from './Pagination.{ext}';\n"
                        "import { useProducts } from '../hooks/useProducts.js';\n\n"
                        "// AI-generated: main feed component\n"
                        "export default function ProductFeed() {\n"
                        "  const [page, setPage] = useState(1);\n"
                        "  const [category, setCategory] = useState('');\n"
                        "  const [search, setSearch] = useState('');\n\n"
                        "  // BUG: filter changes don't reset page to 1\n"
                        "  const { products, loading, error, totalPages } = useProducts({ page, category, search });\n\n"
                        "  return (\n"
                        "    <div>\n"
                        "      <FilterBar category={category} search={search}\n"
                        "        onCategoryChange={setCategory}\n"
                        "        onSearchChange={setSearch} />\n"
                        "      {loading && <p style={{ textAlign: 'center', color: '#94a3b8' }}>Loading products...</p>}\n"
                        "      {error && <p style={{ color: '#ef4444' }}>Error: {error}</p>}\n"
                        "      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1.25rem', margin: '1.5rem 0' }}>\n"
                        "        {products.map(p => <ProductCard key={p.id} product={p} />)}\n"
                        "      </div>\n"
                        "      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_uncontrolled_search",
                "Search input switches between controlled and uncontrolled — React warning and inconsistent behaviour",
                {
                    f"src/components/FilterBar.{ext}": (
                        "// AI-generated: filter bar with category select and search\n"
                        "export default function FilterBar({ category, search, onCategoryChange, onSearchChange }) {\n"
                        "  const categories = ['', 'Electronics', 'Clothing', 'Books', 'Home'];\n"
                        "  return (\n"
                        "    <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>\n"
                        "      <select value={category} onChange={e => onCategoryChange(e.target.value)}\n"
                        "        style={{ padding: '0.45rem 0.75rem', borderRadius: 8, border: '1px solid #e2e8f0', fontSize: '0.875rem' }}>\n"
                        "        {categories.map(c => <option key={c} value={c}>{c || 'All categories'}</option>)}\n"
                        "      </select>\n"
                        "      {/* BUG: value is undefined when search prop is undefined → uncontrolled */}\n"
                        "      <input type='search' placeholder='Search products...' value={search}\n"
                        "        onChange={e => onSearchChange(e.target.value)}\n"
                        "        style={{ flex: 1, minWidth: 180, padding: '0.45rem 0.75rem', borderRadius: 8, border: '1px solid #e2e8f0', fontSize: '0.875rem' }} />\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_pagination_no_aria",
                "Pagination controls have no ARIA labels — screen reader users cannot navigate between pages",
                {
                    f"src/components/Pagination.{ext}": (
                        "// AI-generated: pagination with full accessibility support\n"
                        "export default function Pagination({ page, totalPages, onPageChange }) {\n"
                        "  if (totalPages <= 1) return null;\n"
                        "  return (\n"
                        "    <div style={{ display: 'flex', justifyContent: 'center', gap: '0.4rem', margin: '1rem 0' }}>\n"
                        "      {/* BUG: no aria-label on nav, no aria-current on active page */}\n"
                        "      <button onClick={() => onPageChange(p => Math.max(1, p - 1))} disabled={page === 1}\n"
                        "        style={{ padding: '0.4rem 0.75rem', border: '1px solid #e2e8f0', borderRadius: 8,\n"
                        "          background: page === 1 ? '#f8fafc' : 'white', cursor: page === 1 ? 'default' : 'pointer' }}>‹</button>\n"
                        "      {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => i + 1).map(p => (\n"
                        "        <button key={p} onClick={() => onPageChange(p)}\n"
                        "          style={{ padding: '0.4rem 0.75rem', border: '1px solid #e2e8f0', borderRadius: 8,\n"
                        "            background: p === page ? '#3b82f6' : 'white', color: p === page ? 'white' : '#111' }}>{p}</button>\n"
                        "      ))}\n"
                        "      <button onClick={() => onPageChange(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}\n"
                        "        style={{ padding: '0.4rem 0.75rem', border: '1px solid #e2e8f0', borderRadius: 8,\n"
                        "          background: page === totalPages ? '#f8fafc' : 'white', cursor: page === totalPages ? 'default' : 'pointer' }}>›</button>\n"
                        "    </div>\n"
                        "  );\n}\n"
                    )
                }
            ),
            (
                "bug_no_empty_products",
                "When filter returns no results, nothing is rendered — no empty-state message shown",
                {
                    "src/utils/format.js": (
                        "// AI-generated: formatting utilities\n\n"
                        "export function formatPrice(value, currency = 'USD') {\n"
                        "  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(value);\n"
                        "}\n\n"
                        "export function truncate(str, maxLength = 60) {\n"
                        "  if (!str) return '';\n"
                        "  return str.length > maxLength ? `${str.slice(0, maxLength)}…` : str;\n"
                        "}\n"
                    )
                }
            ),
        ]

        files, issues = self._pick_bugs(bug_pool, n_bugs)
        all_files = {**base, **files}

        all_files[f"src/__tests__/ProductFeed.test.{ext}"] = (
            "import { render, screen, waitFor } from '@testing-library/react';\n"
            f"import ProductFeed from '../components/ProductFeed.{ext}';\n\n"
            "describe('ProductFeed', () => {\n"
            "  test('renders loading state initially', () => {\n"
            "    render(<ProductFeed />);\n"
            "    expect(screen.getByText(/loading/i)).toBeInTheDocument();\n"
            "  });\n"
            "  test('renders products after loading', async () => {\n"
            "    render(<ProductFeed />);\n"
            "    await waitFor(() => expect(screen.queryByText(/loading/i)).not.toBeInTheDocument(), { timeout: 2000 });\n"
            "    expect(screen.getAllByRole('img').length).toBeGreaterThan(0);\n"
            "  });\n"
            "  test('all product images have alt text', async () => {\n"
            "    render(<ProductFeed />);\n"
            "    await waitFor(() => screen.getAllByRole('img'), { timeout: 2000 });\n"
            "    screen.getAllByRole('img').forEach(img => expect(img).toHaveAttribute('alt'));\n"
            "  });\n"
            "});\n"
        )
        all_files["README.md"] = self._readme_api_feed(issues)

        return self._make_result(all_files, issues, "api_feed", "Product Feed", 50)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _pick_bugs(
        self, pool: List[Tuple[str, str, Dict[str, str]]], n: int
    ) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        """Pick n bugs from pool randomly; return merged files dict and issues list."""
        chosen = random.sample(pool, min(n, len(pool)))
        files: Dict[str, str] = {}
        issues: List[Dict[str, Any]] = []
        for bug_id, description, bug_files in chosen:
            files.update(bug_files)
            issues.append({"id": bug_id, "description": description})
        return files, issues

    def _make_result(
        self,
        file_structure: Dict[str, str],
        issues: List[Dict[str, Any]],
        archetype: str,
        display_name: str,
        minutes: int,
    ) -> Dict[str, Any]:
        return {
            "projectStructure": file_structure,
            "projectMetadata": {
                "role": "frontend",
                "displayName": display_name,
                "archetype": archetype,
                "estimatedMinutes": minutes,
            },
            "intentionalIssues": issues,
            "evaluationCriteria": {
                "bug_discovery": "Did the candidate find the intentional issues?",
                "fix_correctness": "Were the fixes correct and complete?",
                "accessibility": "Were accessibility issues addressed?",
                "edge_cases": "Were edge cases considered?",
                "code_quality": "Was overall code quality improved?",
            },
            "candidateInstructions": (
                f"This {display_name} was scaffolded with AI assistance. "
                "The code runs but has bugs, performance issues, and accessibility problems that need to be found and fixed. "
                "Run `npm install && npm run dev` to start. Use `npm test` to see which tests fail. "
                "Document everything you find."
            ),
            "setupInstructions": "npm install && npm run dev",
        }

    # ── README generators ─────────────────────────────────────────────────────

    def _readme_task_board(self, issues: List[Dict[str, Any]]) -> str:
        return self._readme_template(
            "Task Board",
            "You joined a team that used AI to scaffold a Task Board app. The code runs, but there are bugs, "
            "performance issues, and accessibility problems hidden in the codebase. Your job: find and fix them.",
            issues,
        )

    def _readme_dashboard(self, issues: List[Dict[str, Any]]) -> str:
        return self._readme_template(
            "Analytics Dashboard",
            "An analytics dashboard was generated by AI for a SaaS product team. It renders, "
            "but several issues were introduced during generation. Review the code and fix what you find.",
            issues,
        )

    def _readme_form_wizard(self, issues: List[Dict[str, Any]]) -> str:
        return self._readme_template(
            "Onboarding Form Wizard",
            "This multi-step sign-up flow was AI-generated for a product team. "
            "It looks complete but has validation, accessibility, and UX bugs baked in. Find and fix them.",
            issues,
        )

    def _readme_api_feed(self, issues: List[Dict[str, Any]]) -> str:
        return self._readme_template(
            "Product Feed",
            "A product catalog page was AI-generated for a marketplace team. "
            "It fetches and displays data, but has async bugs, accessibility issues, and UX problems. "
            "Your job is to review and fix the code.",
            issues,
        )

    def _readme_template(self, title: str, scenario: str, issues: List[Dict[str, Any]]) -> str:
        return f"""# Frontend AI Fluency Assessment — {title}

## Scenario
{scenario}

## Instructions
1. **Run the app** — `npm install && npm run dev`
2. **Run tests** — `npm test` (some tests will fail — that's intentional)
3. **Find issues** — Use the app, read the code, check the browser console
4. **Fix them** — Correct bugs, improve accessibility, add missing error handling
5. **Document** — Note what you found and how you fixed it in a `FIXES.md` file

## What we're measuring
- Do you critically review AI-generated code before trusting it?
- Can you spot subtle bugs (async, state, hooks, accessibility)?
- Do you fix issues fully or only superficially?
- Do you consider keyboard navigation and screen reader compatibility?
- Do you improve code quality beyond just patching the reported bugs?

Good luck.
"""
