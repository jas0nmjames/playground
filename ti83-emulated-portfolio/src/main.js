/**
 * TI-83+ Emulated Portfolio
 *
 * A nostalgic portfolio experience built as an interactive TI-83+
 * graphing calculator emulator.
 */

// Calculator state
const calculator = {
  display: '',
  mode: 'menu',
  currentMenu: 'main',
  input: '',
};

// Menu data
const menus = {
  main: {
    title: "JASON'S PORTFOLIO",
    separator: "=================",
    options: [
      { key: '1', label: 'PROJECTS', submenu: 'projects' },
      { key: '2', label: 'SKILLS', submenu: 'skills' },
      { key: '3', label: 'ABOUT', submenu: 'about' },
      { key: '4', label: 'CONTACT', submenu: 'contact' },
    ],
  },
  projects: {
    title: 'PROJECTS',
    separator: '========',
    options: [
      { key: '1', label: 'PORTFOLIO SITE' },
      { key: '2', label: 'WEB APPS' },
      { key: '3', label: 'EXPERIMENTS' },
      { key: '0', label: 'BACK' },
    ],
  },
  skills: {
    title: 'SKILLS',
    separator: '======',
    options: [
      { key: '1', label: 'FRONTEND' },
      { key: '2', label: 'BACKEND' },
      { key: '3', label: 'DESIGN' },
      { key: '0', label: 'BACK' },
    ],
  },
  about: {
    title: 'ABOUT',
    separator: '=====',
    content: 'Full-stack designer and\ndeveloper passionate about\ncreating digital experiences.\n\nPress 0 to go back.',
  },
  contact: {
    title: 'CONTACT',
    separator: '=======',
    content: 'Email: jason@example.com\nGitHub: jas0nmjames\nTwitter: @jas0nmjames\n\nPress 0 to go back.',
  },
};

/**
 * Render the current menu to the display
 */
function renderDisplay() {
  const display = document.querySelector('.display');
  const menu = menus[calculator.currentMenu];

  let content = `${menu.title}\n${menu.separator}\n`;

  if (menu.options) {
    content += '\n';
    menu.options.forEach(option => {
      content += `${option.key}: ${option.label}\n`;
    });
    content += '\nENTER CHOICE:';
  } else if (menu.content) {
    content += '\n' + menu.content;
  }

  display.textContent = content;
}

/**
 * Handle number button press
 */
function handleButton(value) {
  if (value === 'CLEAR') {
    calculator.input = '';
  } else if (value === 'ENTER') {
    handleInput(calculator.input);
    calculator.input = '';
  } else {
    calculator.input += value;
  }

  updateDisplay();
}

/**
 * Handle menu input
 */
function handleInput(input) {
  const menu = menus[calculator.currentMenu];

  if (!menu.options) return;

  const selected = menu.options.find(opt => opt.key === input);
  if (selected) {
    if (selected.submenu) {
      calculator.currentMenu = selected.submenu;
    } else if (input === '0') {
      calculator.currentMenu = 'main';
    }
    renderDisplay();
  }
}

/**
 * Update the input display
 */
function updateDisplay() {
  const display = document.querySelector('.display');
  const menu = menus[calculator.currentMenu];

  let content = `${menu.title}\n${menu.separator}\n`;

  if (menu.options) {
    content += '\n';
    menu.options.forEach(option => {
      content += `${option.key}: ${option.label}\n`;
    });
  }

  if (calculator.input) {
    content += `\n> ${calculator.input}`;
  } else {
    content += '\n\nENTER CHOICE:';
  }

  display.textContent = content;
}

/**
 * Initialize the calculator
 */
function init() {
  const buttons = document.querySelectorAll('button');

  buttons.forEach(button => {
    button.addEventListener('click', () => {
      handleButton(button.textContent);
    });
  });

  // Keyboard support
  document.addEventListener('keydown', e => {
    const key = e.key;
    if (/[0-9]/.test(key)) {
      handleButton(key);
    } else if (key === 'Enter') {
      handleButton('ENTER');
    } else if (key === 'Backspace' || key === 'Delete') {
      calculator.input = calculator.input.slice(0, -1);
      updateDisplay();
    } else if (key === 'Escape') {
      handleButton('CLEAR');
    }
  });

  renderDisplay();
}

// Start the application
document.addEventListener('DOMContentLoaded', init);
