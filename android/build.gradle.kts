// ELBIX AIDD Android 루트 빌드 설정
plugins {
    id("com.android.application") version "8.2.2" apply false
    id("com.android.library") version "8.2.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.22" apply false
    id("com.google.dagger.hilt.android") version "2.50" apply false
    id("org.jetbrains.kotlin.plugin.serialization") version "1.9.22" apply false
}

// 전역 설정
buildscript {
    extra.apply {
        set("compileSdk", 34)
        set("minSdk", 26)
        set("targetSdk", 34)
    }
}
