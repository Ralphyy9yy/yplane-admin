// Admin panel JavaScript

let _confirmCallback = null;

/**
 * Open the styled YPlane Confirmation Modal
 */
function showConfirmModal(options) {
  const {
    title = 'Confirm Action',
    message = 'Are you sure you want to proceed?',
    callout = 'This action will take effect immediately.',
    confirmText = 'Proceed',
    confirmType = 'danger', // 'danger' | 'primary' | 'warning'
    icon = 'gpp_maybe',
    btnIcon = 'check',
    formId = null,
    onConfirm = null
  } = options;

  const overlay = document.getElementById('confirm-modal-overlay');
  if (!overlay) {
    if (confirm(message)) {
      if (formId) document.getElementById(formId)?.submit();
      else if (onConfirm) onConfirm();
    }
    return;
  }

  // Set Title & Message
  const titleEl = document.getElementById('confirm-modal-title');
  const descEl = document.getElementById('confirm-modal-desc');
  if (titleEl) titleEl.textContent = title;
  if (descEl) descEl.textContent = message;

  // Set Callout
  const calloutEl = document.getElementById('confirm-modal-callout');
  const calloutTextEl = document.getElementById('confirm-modal-callout-text');
  const calloutIconEl = document.getElementById('confirm-modal-callout-icon');
  if (callout) {
    if (calloutEl) calloutEl.style.display = 'flex';
    if (calloutTextEl) calloutTextEl.textContent = callout;
    if (calloutIconEl) {
      calloutIconEl.textContent = confirmType === 'danger' ? 'warning' : 'info';
      calloutIconEl.style.color = confirmType === 'danger' ? '#dc2626' : '#0f766e';
    }
  } else if (calloutEl) {
    calloutEl.style.display = 'none';
  }

  // Set Header Icon
  const iconWrapper = document.getElementById('confirm-modal-icon-wrapper');
  const iconEl = document.getElementById('confirm-modal-icon');
  if (iconWrapper) iconWrapper.className = `confirm-modal-icon-wrapper ${confirmType}`;
  if (iconEl) iconEl.textContent = icon;

  // Set Submit Button
  const confirmBtn = document.getElementById('confirm-modal-submit-btn');
  const btnLabelEl = document.getElementById('confirm-modal-btn-label');
  const btnIconEl = document.getElementById('confirm-modal-btn-icon');
  if (btnLabelEl) btnLabelEl.textContent = confirmText;
  if (btnIconEl) btnIconEl.textContent = btnIcon;
  if (confirmBtn) {
    confirmBtn.className = confirmType === 'primary' ? 'confirm-submit-btn btn-primary' : 'confirm-submit-btn btn-danger';
  }

  // Register execution handler
  _confirmCallback = () => {
    if (formId) {
      const form = document.getElementById(formId);
      if (form) form.submit();
    } else if (onConfirm) {
      onConfirm();
    }
    closeConfirmModal();
  };

  overlay.classList.add('open');
}

/**
 * Close the styled Confirmation Modal
 */
function closeConfirmModal() {
  const overlay = document.getElementById('confirm-modal-overlay');
  if (overlay) overlay.classList.remove('open');
  _confirmCallback = null;
}

/**
 * Standard confirmation helper for actions
 */
function confirmAction(formId, message, title, btnText, btnType, calloutText, iconName) {
  showConfirmModal({
    formId: formId,
    title: title || 'Confirm Action',
    message: message || 'Are you sure you want to proceed?',
    callout: calloutText || 'This action takes effect immediately.',
    confirmText: btnText || 'Yes, Proceed',
    confirmType: btnType || 'danger',
    icon: iconName || (btnType === 'primary' ? 'check_circle' : 'gpp_maybe'),
    btnIcon: btnType === 'primary' ? 'check' : 'arrow_forward'
  });
}

/**
 * Standard confirmation helper for deletions
 */
function confirmDelete(formId, message, itemName) {
  showConfirmModal({
    formId: formId,
    title: 'Confirm Deletion',
    message: message || `Are you sure you want to permanently delete this item?`,
    callout: 'This record will be permanently deleted from the database.',
    confirmText: 'Delete Record',
    confirmType: 'danger',
    icon: 'delete_forever',
    btnIcon: 'delete'
  });
}

// Global click & keyboard listeners
document.addEventListener('DOMContentLoaded', () => {
  const submitBtn = document.getElementById('confirm-modal-submit-btn');
  if (submitBtn) {
    submitBtn.addEventListener('click', () => {
      if (_confirmCallback) _confirmCallback();
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeConfirmModal();
  });
});

// Flash toast
function showToast(message, type) {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type || 'info'}`;
  toast.style.cssText = 'position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;min-width:280px;max-width:420px;box-shadow:0 8px 24px rgba(0,0,0,0.12);';
  toast.innerHTML = `<span class="material-symbols-outlined">${type === 'error' ? 'error' : 'check_circle'}</span><span>${message}</span>`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// Filter chips
document.querySelectorAll('.filter-chip').forEach(chip => {
  chip.addEventListener('click', function() {
    const group = this.closest('.filter-chips');
    if (group) {
      group.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    }
    this.classList.add('active');
  });
});
