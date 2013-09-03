var LOOKUP_URL_TEMPLATE = "/base/enter_data/lookup_global_id/%s/%s";
var GLOBAL_ID_NOT_FOUND_VAL = "[ not found ]";
var GLOBAL_ID_LABEL_TEMPLATE = "Participant global ID (%s)";

loadGlobalParticipantID = function()
{
  if($('#study-input').val() == "" || $('#study-id-input').val() == "")
    return;

  $("#global-id-label").html(
    sprintf(GLOBAL_ID_LABEL_TEMPLATE, "loading...")
  );

  var studyName = $("#study-input").val();
  var participantStudyID = $("#study-id-input").val();
  var lookupURL = sprintf(LOOKUP_URL_TEMPLATE, studyName, participantStudyID); 
  $.get(lookupURL, function(data) {
    if(data == GLOBAL_ID_NOT_FOUND_VAL)
    {
      $("#global-id-label").html(GLOBAL_ID_LABEL_TEMPLATE.format(
        "Not found. Leave blank to make new ID."));
    }
    else
    {
      $("#global-id-label").html(
        sprintf(GLOBAL_ID_LABEL_TEMPLATE, "ID loaded from server")
      );
      $("#global-id-input").val(data);
    }
  });
};


$(window).load(function () {
  // Apply automatic participant global ID loading
  $("#study-input").blur(loadGlobalParticipantID);
  $("#study-id-input").blur(loadGlobalParticipantID);
});