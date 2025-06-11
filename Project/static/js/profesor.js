function listarProfesor() {
  $.ajax({
    url: "/listarProfesor/",
    type: "get",
    dataType: "json",
    success: function (response) {
      if ($.fn.dataTable.isDataTable("#tabla_profesores")) {
        $("#tabla_profesores").DataTable().clear();
        $("#tabla_profesores").DataTable().destroy();
      }
      $("#tabla_profesores tbody").html("");
      for (let i = 0; i < response.length; i++) {
        let fila = "<tr>";
        fila += "<td>" + (i + 1) + "</td>";
        fila +=
          "<td>" +
          response[i]["fields"]["tipo_cedula_profesor"] +
          response[i]["fields"]["cedula_profesor"] +
          "</td>";
        fila += "<td>" + response[i]["fields"]["nombre_profesor"] + "</td>";
        fila += "<td>" + response[i]["fields"]["apellido_profesor"] + "</td>";
        fila += "<td>" + response[i]["fields"]["telefono_Profesor"] + "</td>";
        fila += "<td>" + response[i]["fields"]["nombre_cargo"] + "</td>";


        fila +=
          '<td><a class = "nav-link w-50 text-lg" title="Editar Profesor" aria-label="Editar Profesor"';
        fila +=
          " onclick = \"abrir_modal_edicionProfesor('/editarProfesor/" +
          response[i]["pk"] +
          '/\');"><i class="fa fa-pencil-square-o fa-2x"></i></a>';
        fila +=
          '<a class = "nav-link w-50 text-lg" title="Eliminar Profesor" aria-label="Eliminar Profesor"';
        fila +=
          " onclick = \"abrir_modal_eliminacionProfesor('/eliminarProfesor/" +
          response[i]["pk"] +
          '/\');"><i class="fa fa-times fa-2x"></i></a>';
        fila += "</tr>";
        $("#tabla_profesores tbody").append(fila);
      }
      $("#tabla_profesores").DataTable({
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
          { data: "Telefono" },
          { data: "Cargo" },

          { data: "Opciones" },
        ],
      });
    },
    error: function (error) {
      console.log(error);
    },
  });
}
function registrarProfesor() {
  activarBoton();
  // Crear un objeto FormData para manejar datos binarios (archivos)
  var formData = new FormData($("#form_creacionProfesor")[0]);
  $.ajax({
    data: formData,
    url: $("#form_creacionProfesor").attr("action"),
    type: $("#form_creacionProfesor").attr("method"),
    processData: false, // No procesar datos (FormData se encargará de ello)
    contentType: false, // No establecer el tipo de contenido (FormData se encargará de ello)
    success: function (response) {
      notificacionSuccessCreacion(response.mensaje);
      listarProfesor();
      cerrar_modal_creacionProfesor();
    },
    error: function (error) {
      notificacionError(error.responseJSON.mensaje);
      mostrarErroresCreacionProfesor(error);
      activarBoton();
    },
  });
}
function editarProfesor() {
  activarBoton();
  // Crear un objeto FormData para manejar datos binarios (archivos)
  var formData = new FormData($("#form_edicionProfesor")[0]);
  $.ajax({
    data: formData,
    url: $("#form_edicionProfesor").attr("action"),
    type: $("#form_edicionProfesor").attr("method"),
    processData: false, // No procesar datos (FormData se encargará de ello)
    contentType: false, // No establecer el tipo de contenido (FormData se encargará de ello)
    success: function (response) {
      notificacionSuccessEdicion(response.mensaje);
      listarProfesor();
      cerrar_modal_edicionProfesor();
    },
    error: function (error) {
      notificacionError(error.responseJSON.mensaje);
      mostrarErroresEdicionProfesor(error);
      activarBoton();
    },
  });
}
function eliminarProfesor(pk) {
  activarBoton();
  $.ajax({
    data: $("#form_eliminacionProfesor").serialize(),
    url: $("#form_eliminacionProfesor").attr("action"),
    type: $("#form_eliminacionProfesor").attr("method"),
    success: function (response) {
      notificacionSuccessEliminacion(response.mensaje);
      listarProfesor();
      cerrar_modal_eliminacionProfesor();
    },
    error: function (error) {
      if (error.responseJSON && error.responseJSON.mensaje) {
        notificacionError(error.responseJSON.mensaje);
      } else {
        notificacionError("Este Profesor tiene relación en otra tabla.");
      }
      cerrar_modal_eliminacionProfesor();
      activarBoton();
    },
  });
}
function abrir_modal_creacionProfesor(url) {
  $("#creacionProfesor").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_creacionProfesor() {
  $("#creacionProfesor").modal("hide");
}
function abrir_modal_edicionProfesor(url) {
  $("#edicionProfesor").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_edicionProfesor() {
  $("#edicionProfesor").modal("hide");
}
function abrir_modal_eliminacionProfesor(url) {
  $("#eliminacionProfesor").load(url, function () {
    $(this).modal("show");
  });
}
function cerrar_modal_eliminacionProfesor() {
  $("#eliminacionProfesor").modal("hide");
}
function mostrarErroresCreacionProfesor(erroresProfesor) {
  $(".error-tipo_cedula_profesor").addClass("d-none");
  $(".error-cedula_profesor").addClass("d-none");
  $(".error-nombre_profesor").addClass("d-none");
  $(".error-apellido_profesor").addClass("d-none");
  $(".error-telefono_Profesor").addClass("d-none");
  $(".error-id_cargo").addClass("d-none");

  for (let item in erroresProfesor.responseJSON.error) {
    let fieldName = item.split(".").pop(); //obtener el nombre del campo
    let errorMessage = erroresProfesor.responseJSON.error[item];
    let errorDiv = $(".error-" + fieldName);
    if (errorMessage !== "") {
      // verificar si el mensaje de error no es vacío
      errorDiv.html(errorMessage);
      errorDiv.removeClass("d-none"); // mostrar el div de alerta
    }
  }
}
function mostrarErroresEdicionProfesor(erroresEdicionProfesor) {
  $(".error-tipo_cedula_profesor").addClass("d-none");
  $(".error-cedula_profesor").addClass("d-none");
  $(".error-nombre_profesor").addClass("d-none");
  $(".error-apellido_profesor").addClass("d-none");
  $(".error-telefono_Profesor").addClass("d-none");
  $(".error-id_cargo").addClass("d-none");

  for (let item in erroresEdicionProfesor.responseJSON.error) {
    let fieldName = item.split(".").pop();
    let errorMessage = erroresEdicionProfesor.responseJSON.error[item];
    let errorDiv = $(".error-" + fieldName);
    if (errorMessage !== "") {
      errorDiv.html(errorMessage);
      errorDiv.removeClass("d-none");
    }
  }
}
$(document).ready(function () {
  listarProfesor();
});
