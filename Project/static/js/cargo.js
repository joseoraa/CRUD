function listarCargo() {
  $.ajax({
    url: "/listarCargo/",
    type: "get",
    dataType: "json",
    success: function (response) {
      if ($.fn.dataTable.isDataTable("#tabla_cargos")) {
        $("#tabla_cargos").DataTable().clear();
        $("#tabla_cargos").DataTable().destroy();
      }
      $("#tabla_cargos tbody").html("");
      for (let i = 0; i < response.length; i++) {
        let fila = "<tr>";
        fila += "<td>" + (i + 1) + "</td>";
        fila += "<td>" + response[i]["fields"]["nombre_cargo"] + "</td>";
        fila +=
          '<td><a class = "nav-link w-50 text-lg" title="Editar Cargo" aria-label="Editar Cargo"';
        fila +=
          " onclick = \"abrir_modal_edicionCargo('/editarCargo/" +
          response[i]["pk"] +
          '/\');"><i class="fa fa-pencil-square-o fa-2x"></i></a>';
        fila +=
          '<a class = "nav-link w-50 text-lg" title="Eliminar Cargo" aria-label="Eliminar Cargo"';
        fila +=
          " onclick = \"abrir_modal_eliminacionCargo('/eliminarCargo/" +
          response[i]["pk"] +
          '/\');"><i class="fa fa-times fa-2x"></i></a>';
        fila += "</tr>";
        $("#tabla_cargos tbody").append(fila);
      }
      $("#tabla_cargos").DataTable({
        language: {
          decimal: "",
          emptyTable: "No hay información",
          info: "Mostrando _START_ a _END_ de _TOTAL_ Entradas",
          infoEmpty: "Mostrando 0 to 0 of 0 Entradas",
          infoFiltered: "(Filtrado de _MAX_ total entradas)",
          infoPostFix: "",
          thousands: ",",
          lengthMenu: "Mostrar _MENU_ Entradas",
          loadingRecords: "Cargando...",
          processing: "Procesando...",
          search: "Buscar:",
          zeroRecords: "Sin resultados encontrados",
          paginate: {
            first: "Primero",
            last: "Ultimo",
            next: "Siguiente",
            previous: "Anterior",
          },
        },
        columns: [{ data: "#" }, { data: "Cargo" }, { data: "Opciones" }],
      });
    },
    error: function (error) {
      console.log(error);
    },
  });
}
function registrarCargo() {
  activarBoton();
  // Crear un objeto FormData para manejar datos binarios (archivos)
  var formData = new FormData($("#form_creacionCargo")[0]);
  $.ajax({
    data: formData,
    url: $("#form_creacionCargo").attr("action"),
    type: $("#form_creacionCargo").attr("method"),
    processData: false, // No procesar datos (FormData se encargará de ello)
    contentType: false, // No establecer el tipo de contenido (FormData se encargará de ello)
    success: function (response) {
      notificacionSuccessCreacion(response.mensaje);
      listarCargo();
      cerrar_modal_creacionCargo();
    },
    error: function (error) {
      notificacionError(error.responseJSON.mensaje);
      mostrarErroresCreacionCargo(error);
      activarBoton();
    },
  });
}
function editarCargo() {
  activarBoton();
  // Crear un objeto FormData para manejar datos binarios (archivos)
  var formData = new FormData($("#form_edicionCargo")[0]);
  $.ajax({
    data: formData,
    url: $("#form_edicionCargo").attr("action"),
    type: $("#form_edicionCargo").attr("method"),
    processData: false, // No procesar datos (FormData se encargará de ello)
    contentType: false, // No establecer el tipo de contenido (FormData se encargará de ello)
    success: function (response) {
      notificacionSuccessEdicion(response.mensaje);
      listarCargo();
      cerrar_modal_edicionCargo();
    },
    error: function (error) {
      notificacionError(error.responseJSON.mensaje);
      mostrarErroresEdicionCargo(error);
      activarBoton();
    },
  });
}
function eliminarCargo(pk) {
  activarBoton();
  $.ajax({
    data: $("#form_eliminacionCargo").serialize(),
    url: $("#form_eliminacionCargo").attr("action"),
    type: $("#form_eliminacionCargo").attr("method"),
    success: function (response) {
      notificacionSuccessEliminacion(response.mensaje);
      listarCargo();
      cerrar_modal_eliminacionCargo();
    },
    error: function (error) {
      if (error.responseJSON && error.responseJSON.mensaje) {
        notificacionError(error.responseJSON.mensaje);
      } else {
        notificacionError("Este Cargo tiene relación en otra tabla.");
      }
      cerrar_modal_eliminacionCargo();
      activarBoton();
    },
  });
}
function abrir_modal_creacionCargo(url) {
  $("#creacionCargo").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_creacionCargo() {
  $("#creacionCargo").modal("hide");
}
function abrir_modal_edicionCargo(url) {
  $("#edicionCargo").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_edicionCargo() {
  $("#edicionCargo").modal("hide");
}
function abrir_modal_eliminacionCargo(url) {
  $("#eliminacionCargo").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_eliminacionCargo() {
  $("#eliminacionCargo").modal("hide");
}
function mostrarErroresCreacionCargo(erroresCargo) {
  $(".error-nombre_cargo").addClass("d-none");
  for (let item in erroresCargo.responseJSON.error) {
    let fieldName = item.split(".").pop(); //obtener el nombre del campo
    let errorMessage = erroresCargo.responseJSON.error[item];
    let errorDiv = $(".error-" + fieldName);
    if (errorMessage !== "") {
      // verificar si el mensaje de error no es vacío
      errorDiv.html(errorMessage);
      errorDiv.removeClass("d-none"); // mostrar el div de alerta
    }
  }
}
function mostrarErroresEdicionCargo(erroresEdicionCargo) {
  $(".error-nombre_cargo").addClass("d-none");
  for (let item in erroresEdicionCargo.responseJSON.error) {
    let fieldName = item.split(".").pop();
    let errorMessage = erroresEdicionCargo.responseJSON.error[item];
    let errorDiv = $(".error-" + fieldName);
    if (errorMessage !== "") {
      errorDiv.html(errorMessage);
      errorDiv.removeClass("d-none");
    }
  }
}
$(document).ready(function () {
  listarCargo();
});
