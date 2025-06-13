

// ADMIN DASHBOARD CHART.JS SCRIPT

const visitsPrescriptionsCtx = document.getElementById('visitsPrescriptionsChart').getContext('2d');
const invoicesCtx = document.getElementById('invoicesChart').getContext('2d');

const visitsPrescriptionsChart = new Chart(visitsPrescriptionsCtx, {
type: 'line',
data: {
    labels: {{ visits_months | tojson | default('[]', true) }},
    datasets: [
        {
            label: 'Visits',
            data: {{ visits_counts | tojson }},
            borderColor: '#0d6efd',
            backgroundColor: 'rgba(13, 110, 253, 0.2)',
            fill: true,
            tension: 0.3
        },
        {
            label: 'Prescriptions',
            data: {{ prescriptions_counts | tojson }},
            borderColor: '#198754',
            backgroundColor: 'rgba(25, 135, 84, 0.2)',
            fill: true,
            tension: 0.3
        }
    ]
},
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'top'
            }
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

const invoicesChart = new Chart(invoicesCtx, {
    type: 'bar',
    data: {
        labels: {{ invoices_months | tojson }},
        datasets: [
            {
                label: 'Total Invoice Amount',
                data: {{ invoices_totals | tojson }},
                backgroundColor: '#dc3545'
            }
        ]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});