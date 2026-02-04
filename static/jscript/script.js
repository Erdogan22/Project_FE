function calculateTotals() {
    for (let day = 1; day <= 31; day++) {

        // Get input elements for this day
        const workInput = document.querySelector(`[name="work_${day}"]`);
        const abs1Input = document.querySelector(`[name="absence1_${day}"]`);
        const abs2Input = document.querySelector(`[name="absence2_${day}"]`);

        const work = parseFloat(workInput.value) || 0;
        const abs1 = parseFloat(abs1Input.value) || 0;
        const abs2 = parseFloat(abs2Input.value) || 0;

        // Calculate total
        const totalCell = document.getElementById(`total_${day}`);
        const total = work + abs1 + abs2;

        // Update total cell
        totalCell.innerText = total > 1 ? "❌" : total;
        totalCell.title = total > 1 ? "⚠️ Total heures > 1!" : `Total: ${total}`;

        // Highlight the total row if needed
        const totalRow = totalCell.parentElement; // <tr> element
        totalRow.style.backgroundColor = total > 1 ? "#f8d7da" : "";

        // Function to color absence cells and add tooltip
        function updateAbsenceCell(td, value) {
            if (!td) return;
            if (value === 1) {
                td.style.backgroundColor = "#e74c3c"; // red
                td.style.color = "white";
                td.title = "Absent toute la journée";
            } else if (value === 0.5) {
                td.style.backgroundColor = "#f9e79f"; // yellow
                td.style.color = "black";
                td.title = "Absent une demi-journée";
            } else {
                td.style.backgroundColor = "white";
                td.style.color = "black";
                td.title = "Présent";
            }
        }

        // Apply coloring and tooltips to Absence1 and Absence2
        updateAbsenceCell(document.getElementById(`abs1_${day}`), abs1);
        updateAbsenceCell(document.getElementById(`abs2_${day}`), abs2);
    }
}

// Attach input event to all table inputs
document.querySelectorAll("input").forEach(input => {
    input.addEventListener("input", calculateTotals);
});

// Run once on page load in case there are pre-filled values
calculateTotals();


// Auto-hide flash messages after 3 seconds
setTimeout(() => {
    const flash = document.querySelector(".flash-success");
    if (flash) flash.style.display = "none";
}, 3000);

// Navbar toggle for mobile view
document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById("navbar-toggle");
    const menu = document.getElementById("navbar-menu");

    toggleButton.addEventListener("click", function () {
        menu.classList.toggle("active");
    });
});