document.addEventListener('DOMContentLoaded', function () {
    // Fetch and update dashboard metrics
    fetch('/api/dashboard_data')
        .then(response => response.json())
        .then(data => {
            document.getElementById('daily-premium').textContent = `₹${data.total_premium.toFixed(2)}`;
        })
        .catch(error => console.error('Error fetching dashboard data:', error));

    fetch('/api/daily_premium')
        .then(response => response.json())
        .then(data => {
            document.getElementById('daily-premium').innerText = `₹${data.daily_premium.toFixed(2)}`;
            document.getElementById('daily-commission').innerText = `₹${(data.daily_premium * 0.05).toFixed(2)}`;
        })
        .catch(error => console.error('Error fetching daily premium:', error));

    fetch('/api/all_time_premium')
        .then(response => response.json())
        .then(data => {
            document.getElementById('all-time-premium').innerText = `₹${data.all_time_premium.toFixed(2)}`;
        })
        .catch(error => console.error('Error fetching all-time premium:', error));

    // Fetch and display chart data
    fetch('/api/user_uploads')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('user-uploads-table');
            const ctx = document.getElementById('user-uploads-chart').getContext('2d');

            tableBody.innerHTML = ''; // Clear existing rows
            const labels = [];
            const values = [];

            data.forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${row.user}</td>
                    <td>${row.uploads}</td>
                    <td>₹${row.total_premium.toFixed(2)}</td>
                `;
                tableBody.appendChild(tr);

                labels.push(row.user);
                values.push(row.total_premium);
            });

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Total Premium (₹)',
                            data: values,
                            backgroundColor: 'rgba(75, 192, 192, 0.6)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                    },
                },
            });
        })
        .catch(error => console.error('Error fetching user upload data:', error));
});