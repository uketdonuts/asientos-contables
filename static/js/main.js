$(document).ready(function() {
    // New SweetAlert2 confirmation for delete buttons
    $(document).on('click', '.delete-button-swal', function(e) {
        e.preventDefault(); // Prevent default link behavior
        var deleteUrl = $(this).attr('href');
        var itemName = $(this).data('item-name') || 'este elemento'; // Get item name or use default

        Swal.fire({
            title: '¿Está seguro?',
            text: `¿Realmente desea eliminar ${itemName}? Esta acción no se puede deshacer.`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                // If confirmed, redirect to the delete URL
                // In a more complex scenario, you might submit a form via AJAX here
                window.location.href = deleteUrl;
            }
        });
    });
});
