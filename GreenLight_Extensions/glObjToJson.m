function json_str = glObjToJson(gl)
    % GLOBJTOJSON Convert a custom MATLAB object "gl" to a JSON string
    %   json_str = glObjToJson(gl) takes a MATLAB object "gl" as input and
    %   returns a JSON string representation of the object.
    %
    %   Inputs:
    %       gl - A MATLAB object that may have nested structures, instances of
    %            the DynamicModel or DynamicElement class, function handles,
    %            or other field types.
    %   Outputs:
    %       json_str - A JSON string representation of the input object "gl".

    % Encode any nested objects within "gl"
    encodedGl = encodeNestedObj(gl);

    % Convert the encoded object to a JSON string using the "jsonencode" function
    json_str = jsonencode(encodedGl);
end

function encodedObj = encodeNestedObj(obj)
    % ENCODENESTEDOBJ Encode a nested MATLAB object into a new object
    %   encodedObj = encodeNestedObj(obj) takes a MATLAB object "obj" as input
    %   and returns an encoded object that can be saved to disk or transmitted
    %   over the network.
    %
    %   Inputs:
    %       obj - A MATLAB object that may have nested structures, instances of
    %             the DynamicModel or DynamicElement class, function handles,
    %             or other field types.
    %   Outputs:
    %       encodedObj - An encoded representation of the input object "obj".

    % If the input object is a struct or an instance of the DynamicModel or DynamicElement class
    if isstruct(obj) || isa(obj, 'DynamicModel') || isa(obj, 'DynamicElement')
        encodedObj = struct();

        % Get the field names of the input object
        fieldNames = fieldnames(obj);

        % Loop through each field in the input object
        for i = 1:numel(fieldNames)
            fieldName = fieldNames{i};
            fieldValue = obj.(fieldName);
            % Encode the field value based on its type
            encodedObj.(fieldName) = encodeFieldValue(fieldName, fieldValue);
        end

    else
        encodedObj = obj; % Store the input object as is in the encoded object
    end

end

function encodedValue = encodeFieldValue(fieldName, fieldValue)
    % ENCODEFIELDVALUE Encode a field value based on its name and type
    %   encodedValue = encodeFieldValue(fieldName, fieldValue) takes a field
    %   name and its value as input arguments and returns an encoded value
    %   based on the field's type. It handles various data types such as
    %   function handles, empty values, structures, and instances of the
    %   DynamicElement class.
    %
    %   Inputs:
    %       fieldName  - The name of the field to be encoded.
    %       fieldValue - The value of the field to be encoded.
    %   Outputs:
    %       encodedValue - The encoded value of the input field value.

    % Check if the field name is 'def' and the field value is a function handle
    if strcmp(fieldName, 'def') && isa(fieldValue, 'function_handle')
        % Convert the function handle to a string
        encodedValue = func2str(fieldValue);
        % Check if the field value is empty
    elseif isempty(fieldValue)
        % Set the encoded value to an empty array
        encodedValue = [];
        % Check if the field value is a structure, DynamicElement object, or a struct
    elseif isstruct(fieldValue) || isa(fieldValue, 'DynamicElement') || isa(fieldValue, 'struct')
        % Encode the nested object
        encodedValue = encodeNestedObj(fieldValue);
        % For all other field value types
    else
        % Set the encoded value to the field value itself
        encodedValue = fieldValue;
    end

end
