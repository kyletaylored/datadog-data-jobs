// Main JavaScript for the Datadog Pipeline Demo

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function () {
    // Auto-refresh functionality for running pipelines
    const pipelineStatus = document.getElementById('pipeline-status');
    if (pipelineStatus &&
        (pipelineStatus.dataset.status === 'running' ||
            pipelineStatus.dataset.status === 'pending')) {

        setTimeout(function () {
            location.reload();
        }, 5000);
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Handle pipeline trigger form submission
    const triggerForm = document.getElementById('trigger-form');
    if (triggerForm) {
        triggerForm.addEventListener('submit', function (e) {
            const submitButton = triggerForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Starting...';
            }
        });
    }
});