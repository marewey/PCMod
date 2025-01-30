import mods.create.SequencedAssemblyManager;

// leather to hides
craftingTable.addShapeless("leather2hide", <item:minecraft:rabbit_hide> * 4, [<item:minecraft:leather>]);

// BASIC BULLET
<recipetype:create:sequenced_assembly>.addRecipe(<recipetype:create:sequenced_assembly>.builder("basic_bullet_create")
 .transitionTo(<item:cgm:basic_bullet>)
 .require(<item:minecraft:gunpowder>)
 .loops(1)
 .addOutput(<item:cgm:basic_bullet> * 64, 100)
 .addOutput(<item:cgm:basic_bullet> * 60, 6)
 .addOutput(<item:minecraft:copper_ingot> * 4, 4)
 .addOutput(<item:minecraft:gunpowder>, 1)
 .addStep<mods.createtweaker.DeployerApplicationRecipe>((rb) => rb.require(<tag:items:forge:ingots/copper>))
 .addStep<mods.createtweaker.DeployerApplicationRecipe>((rb) => rb.require(<tag:items:forge:ingots/copper>))
 .addStep<mods.createtweaker.DeployerApplicationRecipe>((rb) => rb.require(<tag:items:forge:ingots/copper>))
 .addStep<mods.createtweaker.DeployerApplicationRecipe>((rb) => rb.require(<tag:items:forge:ingots/copper>))
 .addStep<mods.createtweaker.CuttingRecipe>((rb) => rb.duration(50)));

//ADVANCED BULLET
<recipetype:create:sequenced_assembly>.addRecipe(<recipetype:create:sequenced_assembly>.builder("advanced_bullet_create")
 .transitionTo(<item:cgm:advanced_bullet>)
 .require(<item:minecraft:gunpowder>)
 .loops(1)
 .addOutput(<item:cgm:advanced_bullet> * 32, 101)
 .addOutput(<item:cgm:advanced_bullet> * 30, 6)
 .addOutput(<item:minecraft:iron_nugget>, 1)
 .addOutput(<item:minecraft:copper_ingot> * 4, 4)
 .addOutput(<item:minecraft:gunpowder>, 1)
 .addStep<mods.createtweaker.DeployerApplicationRecipe>((rb) => rb.require(<tag:items:forge:nuggets/iron>))
 .addStep<mods.createtweaker.DeployerApplicationRecipe>((rb) => rb.require(<tag:items:forge:ingots/copper>))
 .addStep<mods.createtweaker.DeployerApplicationRecipe>((rb) => rb.require(<tag:items:forge:ingots/copper>))
 .addStep<mods.createtweaker.DeployerApplicationRecipe>((rb) => rb.require(<tag:items:forge:ingots/copper>))
 .addStep<mods.createtweaker.DeployerApplicationRecipe>((rb) => rb.require(<tag:items:forge:ingots/copper>))
 .addStep<mods.createtweaker.CuttingRecipe>((rb) => rb.duration(50)));

//SHOTGUN SHELL
<recipetype:create:sequenced_assembly>.addRecipe(<recipetype:create:sequenced_assembly>.builder("shotgun_shell_create")
 .transitionTo(<item:cgm:shell>)
 .require(<item:minecraft:gunpowder>)
 .loops(1)
 .addOutput(<item:cgm:shell> * 48, 101)
 .addOutput(<item:cgm:shell> * 45, 6)
 .addOutput(<item:minecraft:gold_nugget>, 1)
 .addOutput(<item:minecraft:copper_ingot> * 4, 4)
 .addOutput(<item:minecraft:gunpowder>, 1)
 .addStep<mods.createtweaker.DeployerApplicationRecipe>((rb) => rb.require(<tag:items:forge:nuggets/gold>))
 .addStep<mods.createtweaker.DeployerApplicationRecipe>((rb) => rb.require(<tag:items:forge:ingots/copper>))
 .addStep<mods.createtweaker.DeployerApplicationRecipe>((rb) => rb.require(<tag:items:forge:ingots/copper>))
 .addStep<mods.createtweaker.DeployerApplicationRecipe>((rb) => rb.require(<tag:items:forge:ingots/copper>))
 .addStep<mods.createtweaker.DeployerApplicationRecipe>((rb) => rb.require(<tag:items:forge:ingots/copper>))
 .addStep<mods.createtweaker.CuttingRecipe>((rb) => rb.duration(50)));