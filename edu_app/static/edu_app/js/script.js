/*register*/ 
document.addEventListener("DOMContentLoaded", function () {

    const roleSelect = document.getElementById("role");

    const roleSections = {
        student: document.getElementById("student-fields"),
        teacher: document.getElementById("teacher-fields"),
        parent: document.getElementById("parent-fields")
    };

    function updateRoleFields() {

        const selectedRole = roleSelect.value;

        for (const role in roleSections) {

            const section = roleSections[role];

            if (!section) continue;

            const isActive = role === selectedRole;

            section.style.display = isActive ? "block" : "none";

            const fields = section.querySelectorAll("input, select");

            fields.forEach(function (field) {

                field.required = isActive;

                if (!isActive) {
                    field.value = "";
                }

            });
        }
    }

    roleSelect.addEventListener("change", updateRoleFields);

    updateRoleFields();

});

/* Teacher student progress */
document.querySelectorAll('.teacher-progress-fill').forEach(function(bar) {
    let progress = bar.dataset.progress || 0;
    bar.style.width = progress + '%';});