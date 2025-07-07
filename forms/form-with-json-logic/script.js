let logicTree = {};

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
      option.value = c.code;  // ISO code
      option.textContent = c.name;
      countriesSelect.appendChild(option);
    });

    setupListeners();
    setupBranchingLogic();
  });

function setupBranchingLogic() {
  logicTree.questions.forEach(branch => {
    const { id, showIf } = branch;
    const target = document.getElementById(id);

    if (showIf.questionId === "employmentStatus") {
      const inputs = document.querySelectorAll(`input[name="employmentStatus"]`);
      inputs.forEach(radio => {
        radio.addEventListener('change', () => {
          const shouldShow = showIf.values.includes(radio.value);
          target.classList.toggle('hidden', !shouldShow);
        });
      });
    }

    if (showIf.questionId === "use") {
      const checkboxes = document.querySelectorAll(`input[name="use"]`);
      checkboxes.forEach(cb => {
        cb.addEventListener('change', () => {
          const selected = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
          const shouldShow = selected.some(val => showIf.values.includes(val));
          target.classList.toggle('hidden', !shouldShow);
        });
      });
    }
  });
}

function setupListeners() {
  // Income formatting on blur
  const incomeInput = document.getElementById('income');
  incomeInput.addEventListener('blur', () => {
    let raw = incomeInput.value.replace(/[^0-9.]/g, '');
    let num = parseFloat(raw);
    if (isNaN(num)) {
      incomeInput.value = '';
      return;
    }
    incomeInput.value = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(num);
  });

  const form = document.getElementById('kycForm');
  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const useCheckboxes = document.querySelectorAll('input[name="use"]');
    const selectedUse = Array.from(useCheckboxes).filter(cb => cb.checked).map(cb => cb.value);
    const includeCountry = selectedUse.includes('International');

    // Only include occupation if visible
    const occupationField = document.getElementById('q2');
    const occupationValue = !occupationField.classList.contains('hidden')
      ? document.getElementById('occupation').value || null
      : null;

    let incomeRaw = document.getElementById('income').value.replace(/[^0-9.]/g, '');
    let incomeValue = parseFloat(incomeRaw) || 0;

    let countryValues = [];
    if (includeCountry) {
      const selectedOptions = Array.from(document.getElementById('countriesSelect').selectedOptions);
      countryValues = selectedOptions.map(opt => opt.value);
    }

    const data = {
      employmentStatus: form.employmentStatus.value,
      occupation: occupationValue,
      income: incomeValue,
      use: selectedUse,
      countries: includeCountry ? countryValues : []
    };

    showModal(JSON.stringify(data, null, 2));
  });
}

// Modal logic
const modal = document.getElementById("apiModal");
const span = document.getElementsByClassName("close")[0];
function showModal(data) {
  document.getElementById('apiOutput').textContent = data;
  modal.style.display = "block";
}
span.onclick = () => modal.style.display = "none";
window.onclick = e => { if (e.target == modal) modal.style.display = "none"; };
