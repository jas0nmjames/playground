document.addEventListener('DOMContentLoaded', function() {
  const exitModal = document.getElementById('exitModal');
  const proceedButton = document.getElementById('proceedButton');
  const showModalButton = document.getElementById('showModalButton');

  function displayModal() {
    exitModal.style.display = 'block';
  }

  function hideModal() {
    exitModal.style.display = 'none';
    window.open('new_page.html', '_blank');
  }

  showModalButton.addEventListener('click', displayModal);
  proceedButton.addEventListener('click', hideModal);
});