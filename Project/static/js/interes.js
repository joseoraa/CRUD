function listarIntere() {
  $.ajax({
    url: "/listarIntere/",
    type: "get",
    dataType: "json",
    success: function (response) {
      console.log(response); // Aquí es donde agregas console.log para depura
      if ($.fn.dataTable.isDataTable("#tabla_interes")) {
        $("#tabla_interes").DataTable().clear();
        $("#tabla_interes").DataTable().destroy();
      }
      $("#tabla_interes tbody").html("");
      for (let i = 0; i < response.length; i++) {
        let fila = "<tr>";
        fila += "<td>" + (i + 1) + "</td>";
        fila += "<td>" + response[i]["nombre_grupo"] + "</td>";

        fila += "<td>" + response[i]["descripcion_grupo"] + "</td>";
        fila += "<td>" + response[i]["status"] + "</td>";
        fila += "<td>" + response[i]["contador_estudiantes"] + "</td>";

        fila +=
          '<td><a class = "nav-link w-50 text-lg" title="Editar Intere" aria-label="Editar Intere"';

        fila +=
          " onclick = \"abrir_modal_edicionIntere('/editarIntere/" +
          response[i]["id_g"] +
          '/\');"><i class="fa fa-pencil-square-o fa-2x"></i></a>';

        fila +=
          '<a class = "nav-link w-50 text-lg" title="Eliminar Intere" aria-label="Eliminar Intere"';
        fila +=
          " onclick = \"abrir_modal_eliminacionIntere('/eliminarIntere/" +
          response[i]["id_g"] +
          '/\');"><i class="fa fa-times fa-2x"></i></a>';

        fila += "</tr>";

        $("#tabla_interes tbody").append(fila);
      }
      $("#tabla_interes").DataTable({
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
        columns: [
          { data: "#" },
          { data: "Nombre" },

          { data: "Descripcion" },
          { data: "status" },
          { data: "Cantidad de Estudiantes" },
          { data: "Opciones" },
        ],
      });
    },
    error: function (error) {
      console.log(error);
    },
  });
}
function registrarIntere() {
  activarBoton();
  // Crear un objeto FormData para manejar datos binarios (archivos)
  var formData = new FormData($("#form_creacionIntere")[0]);
  $.ajax({
    data: formData,
    url: $("#form_creacionIntere").attr("action"),
    type: $("#form_creacionIntere").attr("method"),
    processData: false, // No procesar datos (FormData se encargará de ello)
    contentType: false, // No establecer el tipo de contenido (FormData se encargará de ello)
    success: function (response) {
      notificacionSuccessCreacion(response.mensaje);
      listarIntere();
      cerrar_modal_creacionIntere();
    },
    error: function (error) {
      notificacionError(error.responseJSON.mensaje);
      mostrarErroresCreacionIntere(error);
      activarBoton();
    },
  });
}
function editarIntere() {
  activarBoton();
  // Crear un objeto FormData para manejar datos binarios (archivos)
  var formData = new FormData($("#form_edicionIntere")[0]);
  $.ajax({
    data: formData,
    url: $("#form_edicionIntere").attr("action"),
    type: $("#form_edicionIntere").attr("method"),
    processData: false, // No procesar datos (FormData se encargará de ello)
    contentType: false, // No establecer el tipo de contenido (FormData se encargará de ello)
    success: function (response) {
      notificacionSuccessEdicion(response.mensaje);
      listarIntere();
      cerrar_modal_edicionIntere();
    },
    error: function (error) {
      notificacionError(error.responseJSON.mensaje);
      mostrarErroresEdicionIntere(error);
      activarBoton();
    },
  });
}
function eliminarIntere(pk) {
  activarBoton();
  $.ajax({
    data: $("#form_eliminacionIntere").serialize(),
    url: $("#form_eliminacionIntere").attr("action"),
    type: $("#form_eliminacionIntere").attr("method"),
    success: function (response) {
      notificacionSuccessEliminacion(response.mensaje);
      listarIntere();
      cerrar_modal_eliminacionIntere();
    },
    error: function (error) {
      if (error.responseJSON && error.responseJSON.mensaje) {
        notificacionError(error.responseJSON.mensaje);
      } else {
        notificacionError("Este Grupo de Interes tiene otro registro.");
      }
      cerrar_modal_eliminacionIntere();
      activarBoton();
    },
  });
}
function abrir_modal_creacionIntere(url) {
  $("#creacionIntere").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_creacionIntere() {
  $("#creacionIntere").modal("hide");
}
function abrir_modal_edicionIntere(url) {
  $("#edicionIntere").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_edicionIntere() {
  $("#edicionIntere").modal("hide");
}
function abrir_modal_eliminacionIntere(url) {
  $("#eliminacionIntere").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_eliminacionIntere() {
  $("#eliminacionIntere").modal("hide");
}
function mostrarErroresCreacionIntere(erroresIntere) {
  $(".error-nombre_grupo").addClass("d-none");
  $(".error-descripcion_grupo").addClass("d-none");
  $(".error-status").addClass("d-none");
  $(".error-contador_estudiantes").addClass("d-none");

  for (let item in erroresIntere.responseJSON.error) {
    let fieldName = item.split(".").pop(); //obtener el nombre del campo
    let errorMessage = erroresIntere.responseJSON.error[item];
    let errorDiv = $(".error-" + fieldName);
    if (errorMessage !== "") {
      // verificar si el mensaje de error no es vacío
      errorDiv.html(errorMessage);
      errorDiv.removeClass("d-none"); // mostrar el div de alerta
    }
  }
}
function mostrarErroresEdicionIntere(erroresEdicionIntere) {
  $(".error-nombre_grupo").addClass("d-none");
  $(".error-descripcion_grupo").addClass("d-none");
  $(".error-status").addClass("d-none");
  $(".error-contador_estudiantes").addClass("d-none");

  for (let item in erroresEdicionIntere.responseJSON.error) {
    let fieldName = item.split(".").pop();
    let errorMessage = erroresEdicionIntere.responseJSON.error[item];
    let errorDiv = $(".error-" + fieldName);
    if (errorMessage !== "") {
      errorDiv.html(errorMessage);
      errorDiv.removeClass("d-none");
    }
  }
}
$(document).ready(function () {
  listarIntere();
});
