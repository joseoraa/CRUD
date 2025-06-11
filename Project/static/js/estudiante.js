function listarEstudiante() {
  $.ajax({
    url: "/listarEstudiante/",
    type: "get",
    dataType: "json",
    success: function (response) {
      if ($.fn.dataTable.isDataTable("#tabla_estudiantes")) {
        $("#tabla_estudiantes").DataTable().clear();
        $("#tabla_estudiantes").DataTable().destroy();
      }
      $("#tabla_estudiantes tbody").html("");
      for (let i = 0; i < response.length; i++) {
        let fila = "<tr>";
        fila += "<td>" + (i + 1) + "</td>";
        fila +=
          "<td>" +
          response[i]["fields"]["tipo_cedula_estudiante"] +
          response[i]["fields"]["cedula_estudiante"] +
          "</td>";
        fila += "<td>" + response[i]["fields"]["nombre_estudiante"] + "</td>";
        fila += "<td>" + response[i]["fields"]["apellido_estudiante"] + "</td>";
        fila += "<td>" + response[i]["fields"]["Sexo"] + "</td>";
        fila += "<td>" + response[i]["fields"]["telefono_estudiante"] + "</td>";
        fila += "<td>" + response[i]["fields"]["correo_estudiante"] + "</td>";
        fila +=
          '<td><a class = "nav-link w-50 text-lg" title="Editar Estudiante" aria-label="Editar Estudiante"';
        fila +=
          " onclick = \"abrir_modal_edicionEstudiante('/editarEstudiante/" +
          response[i]["pk"] +
          '/\');"><i class="fa fa-pencil-square-o fa-2x"></i></a>';
        fila +=
          '<a class = "nav-link w-50 text-lg" title="Eliminar Estudiante" aria-label="Eliminar Estudiante"';
        fila +=
          " onclick = \"abrir_modal_eliminacionEstudiante('/eliminarEstudiante/" +
          response[i]["pk"] +
          '/\');"><i class="fa fa-times fa-2x"></i></a>';
        fila += "</tr>";
        $("#tabla_estudiantes tbody").append(fila);
      }
      $("#tabla_estudiantes").DataTable({
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
          { data: "Cedula" },
          { data: "Nombre" },
          { data: "Apellido" },
          { data: "Sexo" },
          { data: "Telefono" },
          { data: "Correo" },
          { data: "Opciones" },
        ],
      });
    },
    error: function (error) {
      console.log(error);
    },
  });
}
function registrarEstudiante() {
  activarBoton();
  // Crear un objeto FormData para manejar datos binarios (archivos)
  var formData = new FormData($("#form_creacionEstudiante")[0]);
  $.ajax({
    data: formData,
    url: $("#form_creacionEstudiante").attr("action"),
    type: $("#form_creacionEstudiante").attr("method"),
    processData: false, // No procesar datos (FormData se encargará de ello)
    contentType: false, // No establecer el tipo de contenido (FormData se encargará de ello)
    success: function (response) {
      notificacionSuccessCreacion(response.mensaje);
      listarEstudiante();
      cerrar_modal_creacionEstudiante();
    },
    error: function (error) {
      notificacionError(error.responseJSON.mensaje);
      mostrarErroresCreacionEstudiante(error);
      activarBoton();
    },
  });
}
function editarEstudiante() {
  activarBoton();
  // Crear un objeto FormData para manejar datos binarios (archivos)
  var formData = new FormData($("#form_edicionEstudiante")[0]);
  $.ajax({
    data: formData,
    url: $("#form_edicionEstudiante").attr("action"),
    type: $("#form_edicionEstudiante").attr("method"),
    processData: false, // No procesar datos (FormData se encargará de ello)
    contentType: false, // No establecer el tipo de contenido (FormData se encargará de ello)
    success: function (response) {
      notificacionSuccessEdicion(response.mensaje);
      listarEstudiante();
      cerrar_modal_edicionEstudiante();
    },
    error: function (error) {
      notificacionError(error.responseJSON.mensaje);
      mostrarErroresEdicionEstudiante(error);
      activarBoton();
    },
  });
}
function eliminarEstudiante(pk) {
  activarBoton();
  $.ajax({
    data: $("#form_eliminacionEstudiante").serialize(),
    url: $("#form_eliminacionEstudiante").attr("action"),
    type: $("#form_eliminacionEstudiante").attr("method"),
    success: function (response) {
      notificacionSuccessEliminacion(response.mensaje);
      listarEstudiante();
      cerrar_modal_eliminacionEstudiante();
    },
    error: function (error) {
      if (error.responseJSON && error.responseJSON.mensaje) {
        notificacionError(error.responseJSON.mensaje);
      } else {
        notificacionError("Este Estudiante tiene relación en otra tabla.");
      }
      cerrar_modal_eliminacionEstudiante();
      activarBoton();
    },
  });
}
function abrir_modal_creacionEstudiante(url) {
  $("#creacionEstudiante").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_creacionEstudiante() {
  $("#creacionEstudiante").modal("hide");
}
function abrir_modal_edicionEstudiante(url) {
  $("#edicionEstudiante").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_edicionEstudiante() {
  $("#edicionEstudiante").modal("hide");
}
function abrir_modal_eliminacionEstudiante(url) {
  $("#eliminacionEstudiante").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_eliminacionEstudiante() {
  $("#eliminacionEstudiante").modal("hide");
}
function mostrarErroresCreacionEstudiante(erroresEstudiante) {
  $(".error-tipo_cedula_estudiante").addClass("d-none");
  $(".error-cedula_estudiante").addClass("d-none");
  $(".error-nombre_estudiante").addClass("d-none");
  $(".error-apellido_estudiante").addClass("d-none");
  $(".error-Sexo").addClass("d-none");
  $(".error-telefono_estudiante").addClass("d-none");
  $(".error-correo_estudiante").addClass("d-none");
  for (let item in erroresEstudiante.responseJSON.error) {
    let fieldName = item.split(".").pop(); //obtener el nombre del campo
    let errorMessage = erroresEstudiante.responseJSON.error[item];
    let errorDiv = $(".error-" + fieldName);
    if (errorMessage !== "") {
      // verificar si el mensaje de error no es vacío
      errorDiv.html(errorMessage);
      errorDiv.removeClass("d-none"); // mostrar el div de alerta
    }
  }
}

function mostrarErroresEdicionEstudiante(erroresEdicionEstudiante) {
  $(".error-tipo_cedula_estudiante").addClass("d-none");
  $(".error-cedula_estudiante").addClass("d-none");
  $(".error-nombre_estudiante").addClass("d-none");
  $(".error-apellido_estudiante").addClass("d-none");
  $(".error-Sexo").addClass("d-none");
  $(".error-telefono_estudiante").addClass("d-none");
  $(".error-correo_estudiante").addClass("d-none");
  for (let item in erroresEdicionEstudiante.responseJSON.error) {
    let fieldName = item.split(".").pop();
    let errorMessage = erroresEdicionEstudiante.responseJSON.error[item];
    let errorDiv = $(".error-" + fieldName);
    if (errorMessage !== "") {
      errorDiv.html(errorMessage);
      errorDiv.removeClass("d-none");
    }
  }
}

$(document).ready(function () {
  listarEstudiante();
});
