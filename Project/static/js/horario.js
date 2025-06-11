function listarHorario() {
  $.ajax({
    url: "/listarHorario/",
    type: "get",
    dataType: "json",
    success: function (response) {
      if ($.fn.dataTable.isDataTable("#tabla_horarios")) {
        $("#tabla_horarios").DataTable().clear();
        $("#tabla_horarios").DataTable().destroy();
      }
      $("#tabla_horarios tbody").html("");
      for (let i = 0; i < response.length; i++) {
        let fila = "<tr>";
        fila += "<td>" + (i + 1) + "</td>";
        fila +=
          "<td>" +
          response[i]["fields"]["tipo_cedula_profesor"] +
          response[i]["fields"]["cedula_profesor"] +
          " " +
          response[i]["fields"]["nombre_profesor"] +
          " " +
          response[i]["fields"]["apellido_profesor"] +
          "</td>";
        fila += "<td>" + response[i]["fields"]["nombreano"] + "</td>";
        fila += "<td>" + response[i]["fields"]["nombre_grupo"] + "</td>";

        fila += "<td>" + response[i]["fields"]["semana_grupo"] + "</td>";
        fila += "<td>" + response[i]["fields"]["hora_inicio"] + "</td>";
        fila += "<td>" + response[i]["fields"]["hora_final"] + "</td>";

        fila +=
          '<td><a class = "nav-link w-50 text-lg" title="Editar Horario" aria-label="Editar Horario"';
        fila +=
          " onclick = \"abrir_modal_edicionHorario('/editarHorario/" +
          response[i]["pk"] +
          '/\');"><i class="fa fa-pencil-square-o fa-2x"></i></a>';
        fila +=
          '<a class = "nav-link w-50 text-lg" title="Eliminar Horario" aria-label="Eliminar Horario"';
        fila +=
          " onclick = \"abrir_modal_eliminacionHorario('/eliminarHorario/" +
          response[i]["pk"] +
          '/\');"><i class="fa fa-times fa-2x"></i></a>';
        fila += "</tr>";

        $("#tabla_horarios tbody").append(fila);
      }
      $("#tabla_horarios").DataTable({
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
          { data: "Dia" },
          { data: "Hora Inicio" },
          { data: "Hora Final" },
          { data: "Grupo" },
          { data: "Profesor" },
          { data: "Año Escolar" },

          { data: "Opciones" },
        ],
      });
    },
    error: function (error) {
      console.log(error);
    },
  });
}
function registrarHorario() {
  activarBoton();
  // Crear un objeto FormData para manejar datos binarios (archivos)
  var formData = new FormData($("#form_creacionHorario")[0]);
  $.ajax({
    data: formData,
    url: $("#form_creacionHorario").attr("action"),
    type: $("#form_creacionHorario").attr("method"),
    processData: false, // No procesar datos (FormData se encargará de ello)
    contentType: false, // No establecer el tipo de contenido (FormData se encargará de ello)
    success: function (response) {
      notificacionSuccessCreacion(response.mensaje);
      listarHorario();
      cerrar_modal_creacionHorario();
    },
    error: function (error) {
      notificacionError(error.responseJSON.mensaje);
      mostrarErroresCreacionHorario(error);
      activarBoton();
    },
  });
}

function editarHorario() {
  activarBoton();
  // Crear un objeto FormData para manejar datos binarios (archivos)
  var formData = new FormData($("#form_edicionHorario")[0]);
  $.ajax({
    data: formData,
    url: $("#form_edicionHorario").attr("action"),
    type: $("#form_edicionHorario").attr("method"),
    processData: false, // No procesar datos (FormData se encargará de ello)
    contentType: false, // No establecer el tipo de contenido (FormData se encargará de ello)
    success: function (response) {
      notificacionSuccessEdicion(response.mensaje);
      listarHorario();
      cerrar_modal_edicionHorario();
    },
    error: function (error) {
      notificacionError(error.responseJSON.mensaje);
      mostrarErroresEdicionHorario(error);
      activarBoton();
    },
  });
}
function eliminarHorario(pk) {
  activarBoton();
  $.ajax({
    data: $("#form_eliminacionHorario").serialize(),
    url: $("#form_eliminacionHorario").attr("action"),
    type: $("#form_eliminacionHorario").attr("method"),
    success: function (response) {
      notificacionSuccessEliminacion(response.mensaje);
      listarHorario();
      cerrar_modal_eliminacionHorario();
    },
    error: function (error) {
      if (error.responseJSON && error.responseJSON.mensaje) {
        notificacionError(error.responseJSON.mensaje);
      } else {
        notificacionError("Este Horario tiene relación en otra tabla.");
      }
      cerrar_modal_eliminacionHorario();
      activarBoton();
    },
  });
}
function abrir_modal_creacionHorario(url) {
  $("#creacionHorario").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_creacionHorario() {
  $("#creacionHorario").modal("hide");
}
function abrir_modal_edicionHorario(url) {
  $("#edicionHorario").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_edicionHorario() {
  $("#edicionHorario").modal("hide");
}
function abrir_modal_eliminacionHorario(url) {
  $("#eliminacionHorario").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_eliminacionHorario() {
  $("#eliminacionHorario").modal("hide");
}
function mostrarErroresCreacionHorario(erroresHorario) {
  // Primero limpiamos todos los errores anteriores
  $(
    ".error-semana_grupo, .error-hora_inicio, .error-hora_final, .error-id_g, .error-id_p, .error-id_ano"
  )
    .addClass("d-none")
    .html("");

  for (let item in erroresHorario.responseJSON.error) {
    let fieldName = item; // ya no necesitas hacer split
    let errorMessages = erroresHorario.responseJSON.error[item];
    let errorDiv = $(".error-" + fieldName);
    if (errorDiv.length > 0 && errorMessages.length > 0) {
      errorDiv.html(errorMessages.join("<br>"));
      errorDiv.removeClass("d-none");
    } else {
      // Si no hay un div específico para el campo, muestra una notificación general
      notificacionError(errorMessages.join("<br>"));
    }
  }
}

function mostrarErroresEdicionHorario(erroresHorario) {
  // Primero limpiamos todos los errores anteriores
  $(
    ".error-semana_grupo, .error-hora_inicio, .error-hora_final, .error-id_g, .error-id_p, .error-id_ano"
  )
    .addClass("d-none")
    .html("");

  for (let item in erroresHorario.responseJSON.error) {
    let fieldName = item; // ya no necesitas hacer split
    let errorMessages = erroresHorario.responseJSON.error[item];
    let errorDiv = $(".error-" + fieldName);
    if (errorDiv.length > 0 && errorMessages.length > 0) {
      errorDiv.html(errorMessages.join("<br>"));
      errorDiv.removeClass("d-none");
    } else {
      // Si no hay un div específico para el campo, muestra una notificación general
      notificacionError(errorMessages.join("<br>"));
    }
  }
}

$(document).ready(function () {
  listarHorario();
});
