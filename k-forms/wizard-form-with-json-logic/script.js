let logicTree = {};
let questionOrder = ["q1", "q2", "q3", "q4", "q5"];
let historyStack = [];

fetch('logic.json')
  .then(response => response.json())
  .then(data => {
    logicTree = data;

    // Populate Employment Status
    const employmentDiv = document.getElementById('employmentStatusOptions');
    logicTree.employmentStatuses.forEach(status => {
      const label = document.createElement('label');
      label.innerHTML = `<input type="radio" name="employmentStatus" value="${status}" required> ${status}`;
      employmentDiv.appendChild(label);
    });

    // Populate Occupations
    const occupationSelect = document.getElementById('occupation');
    logicTree.occupations.forEach(occ => {
      const option = document.createElement('option');
      option.value = occ;
      option.textContent = occ;
      occupationSelect.appendChild(option);
    });

    // Populate Use Options
    const useDiv = document.getElementById('useOptions');
    logicTree.useOptions.forEach(use => {
      const label = document.createElement('label');
      label.innerHTML = `<input type="checkbox" name="use" value="${use}"> ${use}`;
      useDiv.appendChild(label);
    });

    // Populate Countries
    const countriesSelect = document.getElementById('countriesSelect');
    logicTree.countries.forEach(c => {
      const option = document.createElement('option');
      option.value = c.code;
      option.textContent = c.name;
      countriesSelect.appendChild(option);
    });

    setupListeners();
    historyStack = [0]; // Start with first question index
    showQuestion(0);
  });

function setupListeners() {
  document.getElementById('backButton').addEventListener('click', () => {
    if (document.getElementById('reviewStep').classList.contains('hidden')) {
      if (historyStack.length > 1) {
        historyStack.pop(); // Remove current
        const prevIndex = historyStack[historyStack.length - 1];
        showQuestion(prevIndex);
      }
    } else {
      // Coming back from Review page
      document.getElementById('reviewStep').classList.add('hidden');
      document.getElementById('continueButton').classList.remove('hidden');
      const prevIndex = historyStack[historyStack.length - 1];
      showQuestion(prevIndex);
    }
  });

  document.getElementById('continueButton').addEventListener('click', () => {
    if (isLastQuestion()) {
      showReview();
    } else {
      let nextIndex = historyStack[historyStack.length - 1] + 1;
      showQuestion(nextIndex);
    }
  });

  document.getElementById('editButton').addEventListener('click', () => {
    document.getElementById('reviewStep').classList.add('hidden');
    document.getElementById('continueButton').classList.remove('hidden');
    const prevIndex = historyStack[historyStack.length - 1];
    showQuestion(prevIndex);
  });

  document.getElementById('submitButton').addEventListener('click', () => {
    submitForm();
  });

  document.querySelectorAll('input[name="employmentStatus"]').forEach(radio => {
    radio.addEventListener('change', () => updateBranching());
  });

  document.querySelectorAll('input[name="use"]').forEach(cb => {
    cb.addEventListener('change', () => updateBranching());
  });

  document.getElementById('income').addEventListener('blur', () => {
    let raw = document.getElementById('income').value.replace(/[^0-9.]/g, '');
    let num = parseFloat(raw);
    if (isNaN(num)) {
      document.getElementById('income').value = '';
      return;
    }
    document.getElementById('income').value = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(num);
  });
}

function updateBranching() {
  logicTree.questions.forEach(branch => {
    const { id, showIf } = branch;
    const target = document.getElementById(id);

    if (showIf.questionId === "employmentStatus") {
      const selected = document.querySelector('input[name="employmentStatus"]:checked');
      const shouldShow = selected && showIf.values.includes(selected.value);
      target.dataset.show = shouldShow ? "true" : "false";
    }

    if (showIf.questionId === "use") {
      const selected = Array.from(document.querySelectorAll('input[name="use"]'))
        .filter(cb => cb.checked)
        .map(cb => cb.value);
      const shouldShow = selected.some(val => showIf.values.includes(val));
      target.dataset.show = shouldShow ? "true" : "false";
    }
  });
}

function showQuestion(index) {
  updateBranching();

  questionOrder.forEach(qid => {
    document.getElementById(qid).classList.add('hidden');
  });

  while (index >= 0 && index < questionOrder.length) {
    const qid = questionOrder[index];
    const el = document.getElementById(qid);
    const isHiddenByLogic = el.dataset.show === "false";
    if (!isHiddenByLogic) {
      el.classList.remove('hidden');

      // ✅ Only push if not already last
      if (historyStack[historyStack.length - 1] !== index) {
        historyStack.push(index);
      }
      break;
    } else {
      index++;
    }
  }

  document.getElementById('backButton').classList.toggle('hidden', historyStack.length <= 1);
}

function isLastQuestion() {
  let index = historyStack[historyStack.length - 1];
  while (index + 1 < questionOrder.length) {
    index++;
    const qid = questionOrder[index];
    const el = document.getElementById(qid);
    if (el.dataset.show !== "false") return false;
  }
  return true;
}

function showReview() {
  updateBranching();
  questionOrder.forEach(qid => {
    document.getElementById(qid).classList.add('hidden');
  });

  document.getElementById('reviewStep').classList.remove('hidden');
  document.getElementById('backButton').classList.remove('hidden');
  document.getElementById('continueButton').classList.add('hidden');

  const useCheckboxes = document.querySelectorAll('input[name="use"]');
  const selectedUse = Array.from(useCheckboxes).filter(cb => cb.checked).map(cb => cb.value);
  const includeCountry = selectedUse.includes('International');

  const occupationField = document.getElementById('q2');
  const occupationValue = occupationField.dataset.show !== "false"
    ? document.getElementById('occupation').value || "(none)" : "(hidden)";

  let incomeRaw = document.getElementById('income').value.replace(/[^0-9.]/g, '');
  let incomeValue = parseFloat(incomeRaw) || 0;

  let countryValues = [];
  if (includeCountry) {
    const selectedOptions = Array.from(document.getElementById('countriesSelect').selectedOptions);
    countryValues = selectedOptions.map(opt => opt.value);
  }

  const data = {
    "Employment Status": document.querySelector('input[name="employmentStatus"]:checked').value,
    "Occupation": occupationValue,
    "Income": `$${incomeValue.toLocaleString()}`,
    "Use": selectedUse.join(", "),
    "Countries": includeCountry ? countryValues.join(", ") : "(none)"
  };

  let html = `<ul>`;
  for (const [key, val] of Object.entries(data)) {
    html += `<li><strong>${key}:</strong> ${val}</li>`;
  }
  html += `</ul>`;
  document.getElementById('summaryOutput').innerHTML = html;
}

function submitForm() {
  const useCheckboxes = document.querySelectorAll('input[name="use"]');
  const selectedUse = Array.from(useCheckboxes).filter(cb => cb.checked).map(cb => cb.value);
  const includeCountry = selectedUse.includes('International');

  const occupationField = document.getElementById('q2');
  const occupationValue = occupationField.dataset.show !== "false"
    ? document.getElementById('occupation').value || null : null;

  let incomeRaw = document.getElementById('income').value.replace(/[^0-9.]/g, '');
  let incomeValue = parseFloat(incomeRaw) || 0;

  let countryValues = [];
  if (includeCountry) {
    const selectedOptions = Array.from(document.getElementById('countriesSelect').selectedOptions);
    countryValues = selectedOptions.map(opt => opt.value);
  }

  const data = {
    employmentStatus: document.querySelector('input[name="employmentStatus"]:checked').value,
    occupation: occupationValue,
    income: incomeValue,
    use: selectedUse,
    countries: includeCountry ? countryValues : []
  };

  showModal(JSON.stringify(data, null, 2));
}

const modal = document.getElementById("apiModal");
const span = document.getElementsByClassName("close")[0];
function showModal(data) {
  document.getElementById('apiOutput').textContent = data;
  modal.style.display = "block";
}
span.onclick = () => modal.style.display = "none";
window.onclick = e => { if (e.target == modal) modal.style.display = "none"; };
