# KYC Multi-Step Questionnaire

This is a simple Know Your Customer (KYC) banking questionnaire web form built with vanilla HTML, CSS, and JavaScript.  
It demonstrates a multi-step form with dynamic branching logic, a final review step, and a clean JSON payload preview.

---

## ✨ Features

✅ **One question per page** — multi-step wizard style  
✅ **Branching logic** — driven by `logic.json` so you can show/hide questions based on answers  
✅ **Full ISO country list** — supports multiple countries for international use  
✅ **Always "Continue"** — navigation uses a single clear button label  
✅ **Final review page** — users can review and edit answers before submitting  
✅ **Clean JSON output** — shows exactly what would be sent in an API POST

---

## 📂 Project Structure

/kyc-multistep-review/
├── index.html # The main form page
├── styles.css # Basic styling
├── script.js # Dynamic logic & navigation
├── logic.json # All branching rules and options
├── README.md # This file

---

## ⚙️ How to Use

1. **Open `index.html`** in your browser.
2. Answer each question one at a time.
3. Use **Back** and **Continue** to navigate.
4. On the final **Review** screen, check your answers.
5. Click **Go Back and Edit** if needed, or **Submit** to see the JSON preview.

---

## ⚡ Customization

- **Logic & options**: Edit `logic.json` to change questions, options, or branching logic.
- **Occupations and country list**: Fully editable, uses standard ISO codes.
- **No frameworks**: 100% vanilla HTML, CSS, and JavaScript.

---

## 🤝 Attribution

> **This project was created with the help of [ChatGPT](https://openai.com/chatgpt)** —  
> an AI language model developed by OpenAI — for planning, code generation, and best practices.

---

## 📄 License

This is an educational and demonstration project.  
Feel free to adapt it for learning or internal use.  
Always validate, test thoroughly, and review for your production environment.

---

Happy onboarding! 🎉✨
