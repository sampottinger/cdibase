/**
 * Client-side logic for entering a completed CDI.
 *
 * Copyright (C) 2014 A. Samuel Pottinger ("Sam Pottinger", gleap.org)
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
**/


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
      $("#global-id-label").html(sprintf(GLOBAL_ID_LABEL_TEMPLATE,
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