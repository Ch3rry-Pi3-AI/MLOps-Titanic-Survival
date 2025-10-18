# 🎨 **Templates — Titanic Survival Prediction App**

This folder contains the **HTML templates** rendered by the Flask application.

The main file, **`index.html`**, defines the full web interface — including:
- A **two-column layout** for passenger input and model outputs  
- A **data drift summary table** powered by *Alibi Detect*  
- Conditional sections for displaying **prediction results**, **probabilities**, and **errors**  
- Dynamic rendering via **Jinja2** placeholders (e.g., `{{ prediction_label }}`, `{{ drift.rows }}`)

## 🧱 Structure

```

templates/
└── index.html   # Main app UI with prediction + drift results

```

## 💡 Notes
- Keep field IDs aligned with backend form names (`Age`, `Fare`, `Pclass`, etc.).
- Styling and layout are managed in `../static/style.css`.
- Uses semantic HTML elements (`<header>`, `<main>`, `<section>`) for accessibility.
