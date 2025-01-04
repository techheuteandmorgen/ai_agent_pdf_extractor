document.addEventListener('DOMContentLoaded', function () {
    // Fetch and update dashboard metrics
    fetch('/api/dashboard_data')
        .then(response => response.json())
        .then(data => {
            document.getElementById('daily-premium').textContent = `₹${data.daily_premium || 0}`;
            document.getElementById('daily-commission').textContent = `₹${data.daily_commission || 0}`;
            document.getElementById('all-time-premium').textContent = `₹${data.total_premium || 0}`;
        })
        .catch(error => console.error('Error fetching dashboard data:', error));

    // Fetch and display user upload summary and chart
    fetch('/api/user_uploads')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('user-uploads-table');
            const ctx = document.getElementById('user-uploads-chart').getContext('2d');

            // Clear and populate table
            tableBody.innerHTML = '';
            const labels = [];
            const values = [];

            data.forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${row.username}</td>
                    <td>${row.uploads}</td>
                    <td>₹${row.total_premium || 0}</td>
                    <td>₹${row.commission || 0}</td>
                    <td>₹${row.net_premium || 0}</td>
                `;
                tableBody.appendChild(tr);

                labels.push(row.username);
                values.push(row.total_premium);
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
                }
            });
        })
        .catch(error => console.error('Error fetching user uploads:', error));
});