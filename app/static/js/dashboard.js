document.addEventListener('DOMContentLoaded', function () {
    // Fetch and update dashboard metrics
    fetch('/api/dashboard_data')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch dashboard data');
            }
            return response.json();
        })
        .then(data => {
            const dailyPremiumElem = document.getElementById('daily-premium');
            const dailyCommissionElem = document.getElementById('daily-commission');
            const allTimePremiumElem = document.getElementById('all-time-premium');

            if (dailyPremiumElem) {
                dailyPremiumElem.textContent = `₹${data.daily_premium || 0}`;
            } else {
                console.error('Element with ID "daily-premium" not found.');
            }

            if (dailyCommissionElem) {
                dailyCommissionElem.textContent = `₹${data.daily_commission || 0}`;
            } else {
                console.error('Element with ID "daily-commission" not found.');
            }

            if (allTimePremiumElem) {
                allTimePremiumElem.textContent = `₹${data.total_premium_all_time || 0}`;
            } else {
                console.error('Element with ID "all-time-premium" not found.');
            }
        })
        .catch(error => console.error('Error fetching dashboard data:', error));

    // Fetch and display user upload summary and chart
    fetch('/api/user_uploads')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch user uploads');
            }
            return response.json();
        })
        .then(data => {
            const tableBody = document.getElementById('user-uploads-table');
            const chartCanvas = document.getElementById('user-uploads-chart');

            if (!tableBody) {
                console.error('Element with ID "user-uploads-table" not found.');
                return;
            }

            if (!chartCanvas) {
                console.error('Element with ID "user-uploads-chart" not found.');
                return;
            }

            const ctx = chartCanvas.getContext('2d');

            // Clear and populate table
            tableBody.innerHTML = '';
            const labels = [];
            const values = [];

            data.forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${row.username || 'N/A'}</td>
                    <td>${row.uploads || 0}</td>
                    <td>₹${row.total_premium || 0}</td>
                    <td>₹${row.commission || 0}</td>
                    <td>₹${row.net_premium || 0}</td>
                `;
                tableBody.appendChild(tr);

                labels.push(row.username || 'N/A');
                values.push(row.total_premium || 0);
            });

            // Generate chart
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Total Premium (₹)',
                        data: values,
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error fetching user uploads:', error));
});
