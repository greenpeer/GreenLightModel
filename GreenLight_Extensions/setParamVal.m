function setParamVal(dm, attrib, name, val)
    % SETPARAMVAL sets a parameter value for a specific attribute and name within a dynamic model (dm) object.
    if islogical(val)
        % If true, convert the logical value to its numerical equivalent (1 for true, 0 for false)
        val = 1 * val;
    end

    % Check if the input value is of numeric data type
    if isnumeric(val)
        % Check if the input value is empty, a scalar, or a matrix with 2 column
        if isempty(val) || isscalar(val) || size(val, 2) == 2
            % If the conditions are met, set the parameter value in the dynamic model object
            dm.(attrib).(name).val = val;
        else
            % If the input value does not meet the conditions, throw an error message
            error('Argument for DynamicElement value must be empty, a scalar, or a matrix with 2 columns');
        end

    else
        % If the input value is not numeric, throw an error message
        error('Argument for DynamicElement value must be numeric');
    end

end
