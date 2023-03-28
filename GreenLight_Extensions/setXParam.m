function setXParam(dm, name, val)
    % SETXPARAM Change value of a parameter in a DynamicModel object.
    % Throws an error if DynamicElement of 'dm.x.<name>' doesn't exist.
    % Inputs:
    %   dm - A DynamicModel object
    %   name - The name of the parameter to be changed
    %   val - The new value that the parameter receives
    % Throws:
    %   If the model does not have a parameter named 'name'.
    %   If the given value isn't numeric.

    % Throw error if DynamicElement of 'dm.x.<name>' doesn't exist

    % Throw error if DynamicElement of 'dm.x.<name>' doesn't exist
    assert(isfield(dm.x, name), "The model has no parameter named '%s'", name);
    % Throw error if the given value isn't numeric
    assert(isnumeric(val), "The given value must be numeric");

    % Change the value of the parameter
    dm.x.(name).val = val;
end
