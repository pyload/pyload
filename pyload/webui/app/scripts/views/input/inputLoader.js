define(['utils/apitypes', './textInput', './clickInput'], function(Api, textInput, clickInput) {
  'use strict';

  // selects appropriate input element
  return function(input) {
    console.log('Select input', input);

    if (input.type == Api.InputType.Click)
      return clickInput;

    return textInput;
  };
});
