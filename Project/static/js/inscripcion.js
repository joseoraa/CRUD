function listarInscripcion() {
  $.ajax({
    url: "/listarInscripcion/",
    type: "get",
    dataType: "json",
    success: function (response) {
      if ($.fn.dataTable.isDataTable("#tabla_inscripciones")) {
        $("#tabla_inscripciones").DataTable().clear();
        $("#tabla_inscripciones").DataTable().destroy();
      }
      $("#tabla_inscripciones tbody").html("");
      for (let i = 0; i < response.length; i++) {
        let fila = "<tr>";
        fila += "<td>" + (i + 1) + "</td>";
        fila +=
          "<td>" +
          response[i]["fields"]["tipo_cedula_estudiante"] +
          response[i]["fields"]["cedula_estudiante"] +
          " " +
          response[i]["fields"]["nombre_estudiante"] +
          " " +
          response[i]["fields"]["apellido_estudiante"] +
          "</td>";

        fila += "<td>" + response[i]["fields"]["ano_curso"] + "</td>";
        fila += "<td>" + response[i]["fields"]["seccion"] + "</td>";
        fila += "<td>" + response[i]["fields"]["nombre_grupo"] + "</td>";
        fila += "<td>" + response[i]["fields"]["nombreano"] + "</td>";
        fila +=
          '<td><a class = "nav-link w-50 text-lg" title="Editar Inscripcion" aria-label="Editar Inscripcion"';
        fila +=
          " onclick = \"abrir_modal_edicionInscripcion('/editarInscripcion/" +
          response[i]["pk"] +
          '/\');"><i class="fa fa-pencil-square-o fa-2x"></i></a>';
        fila +=
          '<a class = "nav-link w-50 text-lg" title="Eliminar Inscripcion" aria-label="Eliminar Inscripcion"';
        fila +=
          " onclick = \"abrir_modal_eliminacionInscripcion('/eliminarInscripcion/" +
          response[i]["pk"] +
          '/\');"><i class="fa fa-times fa-2x"></i></a>';

        fila += "</tr>";

        $("#tabla_inscripciones tbody").append(fila);
      }
      $("#tabla_inscripciones").DataTable({
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
          { data: "Estudiante" },
          { data: "seccion" },
          { data: "año" },
          { data: "año " },

          { data: "Grupo" },
          { data: "Opciones" },
        ],
      });
    },
    error: function (error) {
      console.log(error);
    },
  });
}
function registrarInscripcion() {
  activarBoton();
  // Crear un objeto FormData para manejar datos binarios (archivos)
  var formData = new FormData($("#form_creacionInscripcion")[0]);
  $.ajax({
    data: formData,
    url: $("#form_creacionInscripcion").attr("action"),
    type: $("#form_creacionInscripcion").attr("method"),
    processData: false, // No procesar datos (FormData se encargará de ello)
    contentType: false, // No establecer el tipo de contenido (FormData se encargará de ello)
    success: function (response) {
      notificacionSuccessCreacion(response.mensaje);
      listarInscripcion();
      cerrar_modal_creacionInscripcion();
    },
    error: function (error) {
      notificacionError(error.responseJSON.mensaje);
      mostrarErroresCreacionInscripcion(error);
      activarBoton();
    },
  });
}
function editarInscripcion() {
  activarBoton();
  // Crear un objeto FormData para manejar datos binarios (archivos)
  var formData = new FormData($("#form_edicionInscripcion")[0]);
  $.ajax({
    data: formData,
    url: $("#form_edicionInscripcion").attr("action"),
    type: $("#form_edicionInscripcion").attr("method"),
    processData: false, // No procesar datos (FormData se encargará de ello)
    contentType: false, // No establecer el tipo de contenido (FormData se encargará de ello)
    success: function (response) {
      notificacionSuccessEdicion(response.mensaje);
      listarInscripcion();
      cerrar_modal_edicionInscripcion();
    },
    error: function (error) {
      notificacionError(error.responseJSON.mensaje);
      mostrarErroresEdicionInscripcion(error);
      activarBoton();
    },
  });
}
function eliminarInscripcion(pk) {
  activarBoton();
  $.ajax({
    data: $("#form_eliminacionInscripcion").serialize(),
    url: $("#form_eliminacionInscripcion").attr("action"),
    type: $("#form_eliminacionInscripcion").attr("method"),
    success: function (response) {
      notificacionSuccessEliminacion(response.mensaje);
      listarInscripcion();
      cerrar_modal_eliminacionInscripcion();
    },
    error: function (error) {
      if (error.responseJSON && error.responseJSON.mensaje) {
        notificacionError(error.responseJSON.mensaje);
      } else {
        notificacionError("Este Estudiante tiene registro previo.");
      }
      cerrar_modal_eliminacionInscripcion();
      activarBoton();
    },
  });
}
function abrir_modal_creacionInscripcion(url) {
  $("#creacionInscripcion").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_creacionInscripcion() {
  $("#creacionInscripcion").modal("hide");
}
function abrir_modal_edicionInscripcion(url) {
  $("#edicionInscripcion").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_edicionInscripcion() {
  $("#edicionInscripcion").modal("hide");
}
function abrir_modal_eliminacionInscripcion(url) {
  $("#eliminacionInscripcion").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_eliminacionInscripcion() {
  $("#eliminacionInscripcion").modal("hide");
}
function ocultarErroresInscripcion() {
  const campos = ["id_estudiante", "seccion", "ano_curso", "id_ano", "id_g"];
  campos.forEach((campo) => {
    $(".error-" + campo)
      .addClass("d-none")
      .html(""); // ocultar y limpiar
  });
}
function mostrarErroresCreacionInscripcion(errores) {
  ocultarErroresInscripcion();
  const erroresJSON = errores.responseJSON?.error || {};
  for (let item in erroresJSON) {
    const fieldName = item === "__all__" ? "form" : item;
    const errorMessage = erroresJSON[item];
    if (fieldName === "form") {
      $(".error-form")
        .html(errorMessage)
        .removeClass("d-none");
    } else {
      $(".error-" + fieldName)
        .html(errorMessage)
        .removeClass("d-none");
    }
  }
}
function mostrarErroresEdicionInscripcion(errores) {
  ocultarErroresInscripcion();
  const erroresJSON = errores.responseJSON?.error || {};
  for (let item in erroresJSON) {
    const fieldName = item === "__all__" ? "form" : item;
    const errorMessage = erroresJSON[item];
    if (fieldName === "form") {
      $(".error-form")
        .html(errorMessage)
        .removeClass("d-none");
    } else {
      $(".error-" + fieldName)
        .html(errorMessage)
        .removeClass("d-none");
    }
  }
}


$(document).ready(function () {
  listarInscripcion();
});
