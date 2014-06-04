# In order yo use Parse you need to do the following.

1. Download the Parse SDK
2. Select your Project > Build Phases
3. You need to import a bunch of libs to get Parse working e.g. SystemConfiguration.framework, StoreKit.framework, Security.framework, QuartzCore.framework, MobileCoreServices.framework, libz.dylib, CoreLocation.framework, CoreGraphics.framework, CFNetwork.framework and finally AudioToolbox.framework
4. You need to create a Swift.h file with the line ``` #import <Parse/Parse.h> ```
5. You will need to reference the Swift.h file within Swift Compiler - Code Generation under Build Settings

